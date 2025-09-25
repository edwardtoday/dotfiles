local M = {}

local enableScript = os.getenv("HOME") .. "/.bin/enable_wired_subnets.sh"
local disableScript = os.getenv("HOME") .. "/.bin/disable_wired_subnets.sh"
local expectedGateway = "192.168.233.1"

local wiredRouteEnabled = false
local lastWiredNow = nil
local lastGateway = nil
local lastIP = nil

function M.runShellScript(script)
    local output, status, t, rc = hs.execute(script)
    hs.notify.new({
        title = "Hammerspoon",
        informativeText = "执行: " .. script
            .. "\n状态: " .. tostring(status)
            .. "\n类型: " .. tostring(t)
            .. "\n退出码: " .. tostring(rc)
            .. "\n输出: " .. (output or "")
    }):send()
    hs.printf("[Hammerspoon] 脚本执行: %s\n状态: %s\n类型: %s\n退出码: %s\n输出: %s",
        script, tostring(status), tostring(t), tostring(rc), output or "")
end

function M.getEn7Gateway()
    local output = hs.execute([[netstat -rn | awk '$4=="en7" && $1=="default" {print $2}']])
    local gw = output and output:gsub("%s+", "") or ""
    return gw
end

function M.isWiredConnected()
    local details = hs.network.interfaceDetails("en7")
    local hasIPv4 = details and details["IPv4"] ~= nil
    local ip = hasIPv4 and details["IPv4"].Addresses[1] or ""
    local gw = M.getEn7Gateway()
    local isRightGW = (gw == expectedGateway)
    return hasIPv4 and isRightGW, gw, ip
end

function M.updateWiredRoute()
    local wiredNow, gw, ip = M.isWiredConnected()
    if wiredNow ~= lastWiredNow or gw ~= lastGateway or ip ~= lastIP then
        hs.printf("[Hammerspoon] en7状态变更: wiredRouteEnabled=%s, 检测en7连线=%s, 网关=%s, IP=%s", tostring(wiredRouteEnabled), tostring(wiredNow), gw or "", ip or "")
        lastWiredNow = wiredNow
        lastGateway = gw
        lastIP = ip
    end

    if wiredNow then
        if not wiredRouteEnabled then
            M.runShellScript("bash '" .. enableScript .. "'")
            wiredRouteEnabled = true
            hs.notify.new({title="Hammerspoon", informativeText="有线子网路由已启用"}):send()
        end
    else
        if wiredRouteEnabled then
            M.runShellScript("bash '" .. disableScript .. "'")
            wiredRouteEnabled = false
            hs.notify.new({title="Hammerspoon", informativeText="有线子网路由已禁用"}):send()
        end
    end
end

function M.start()
    -- 用 xpcall 包裹，任何异常都不会中断定时器
    hs.timer.doEvery(2, function()
        local ok, msg = xpcall(M.updateWiredRoute, debug.traceback)
        if not ok then
            hs.printf("[Hammerspoon] updateWiredRoute error: %s", msg)
        end
    end)
    M.updateWiredRoute()
end

return M
