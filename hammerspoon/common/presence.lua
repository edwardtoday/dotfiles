local M = {}

local function lidIsOpen()
    local output = hs.execute("/usr/sbin/ioreg -r -k AppleClamshellState -d 4")
    if not output or output == "" then
        return true
    end
    return not output:match('"AppleClamshellState"%s*=%s*Yes')
end

local function requireToken(config)
    if config.token and config.token ~= "" then
        return config.token
    end
    error("presence token is missing from ~/.hammerspoon-local.lua")
end

function M.start(config)
    local token = requireToken(config)

    if config.role == "sender" then
        local enabled = true
        local socket = hs.socket.udp.new()

        local function sendHeartbeat()
            if enabled and lidIsOpen() then
                socket:send(token, config.miniHost, config.port)
            end
        end

        local watcher = hs.caffeinate.watcher.new(function(event)
            if event == hs.caffeinate.watcher.screensDidLock
                or event == hs.caffeinate.watcher.systemWillSleep
                or event == hs.caffeinate.watcher.sessionDidResignActive then
                enabled = false
            elseif event == hs.caffeinate.watcher.screensDidUnlock
                or event == hs.caffeinate.watcher.systemDidWake
                or event == hs.caffeinate.watcher.sessionDidBecomeActive then
                enabled = true
                sendHeartbeat()
            end
        end)

        watcher:start()
        sendHeartbeat()
        M.timer = hs.timer.doEvery(config.interval, sendHeartbeat)
        M.watcher = watcher
        return
    end

    local lastHeartbeat = nil
    local startedAt = hs.timer.secondsSinceEpoch()
    local mbpPresent = nil
    local lockedForAbsence = false

    local function setPresent(present)
        if mbpPresent == present then
            return
        end

        mbpPresent = present
        if present then
            hs.caffeinate.set("displayIdle", true)
            hs.caffeinate.declareUserActivity()
            lockedForAbsence = false
            print("MBP present: prevent auto lock")
        else
            hs.caffeinate.set("displayIdle", false)
            if not lockedForAbsence then
                lockedForAbsence = true
                print("MBP absent: lock mini")
                hs.caffeinate.lockScreen()
            end
        end
    end

    local server = hs.socket.udp.server(config.port, function(data)
        if data == token then
            lastHeartbeat = hs.timer.secondsSinceEpoch()
            setPresent(true)
        end
    end)
    server:receive()

    M.server = server
    M.timer = hs.timer.doEvery(2, function()
        local now = hs.timer.secondsSinceEpoch()
        if lastHeartbeat then
            if now - lastHeartbeat > config.absenceTimeout then
                setPresent(false)
            end
        elseif now - startedAt > config.startupGrace then
            setPresent(false)
        end
    end)
end

return M
