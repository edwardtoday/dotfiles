local M = {}

local function stopTimer(timer)
    if timer then
        timer:stop()
    end
end

local function displayFor(config)
    return hs.screen.find(config.displayName)
end

local function currentDisplayPosition(config, screen)
    local point = hs.mouse.absolutePosition()
    local frame = screen:fullFrame()
    local distance = config.role == "mbp"
        and (point.x - frame.x)
        or ((frame.x + frame.w) - point.x)
    local current = hs.mouse.getCurrentScreen()
    local onDisplay = current and current:id() == screen:id()
    return point, distance, onDisplay
end

local function runDDC(config, done)
    print(string.format("display handoff: %s -> %s (%s)", config.role, config.targetLabel, config.targetInput))
    local task = hs.task.new(
        config.ddc,
        function(exitCode, stdOut, stdErr)
            if exitCode == 0 then
                done(true, stdOut or "")
            else
                print(string.format(
                    "display handoff failed: exit=%s stderr=%s stdout=%s",
                    tostring(exitCode), stdErr or "", stdOut or ""
                ))
                done(false, stdErr or stdOut or "")
            end
        end,
        nil,
        {"display", config.displayUUID, "set", "input", config.targetInput}
    )
    if not task:start() then
        print("display handoff failed: unable to start m1ddc")
        done(false, "unable to start m1ddc")
    end
end

local function readInput(config, done)
    local task = hs.task.new(
        config.ddc,
        function(exitCode, stdOut, stdErr)
            if exitCode == 0 then
                done(tonumber((stdOut or ""):match("%d+")), stdOut or "")
            else
                done(nil, stdErr or stdOut or "")
            end
        end,
        nil,
        {"display", config.displayUUID, "get", "input"}
    )
    if not task:start() then
        done(nil, "unable to start m1ddc readback")
    end
end

function M.start(config)
    local armed = false
    local lastX = nil
    local pending = nil
    local pendingMonitor = nil
    local switchInFlight = false
    local cooldownUntil = 0

    local movingTowardEdge = config.role == "mbp" and function(dx)
        return dx < 0
    end or function(dx)
        return dx > 0
    end

    local function cancelPending(reason, rearm)
        stopTimer(pending)
        stopTimer(pendingMonitor)
        pending = nil
        pendingMonitor = nil
        if rearm then
            armed = true
        end
        print("display handoff cancelled: " .. reason)
    end

    local function startSwitch()
        if switchInFlight then
            return
        end

        switchInFlight = true
        runDDC(config, function(ok)
            switchInFlight = false
            if ok then
                cooldownUntil = hs.timer.secondsSinceEpoch() + config.cooldown
                readInput(config, function(input)
                    if input then
                        print(string.format("display handoff readback: input=%s", tostring(input)))
                    end
                end)
            else
                armed = true
            end
        end)
    end

    local function cancelIfMouseMovedBack()
        if not pending then
            return
        end

        local screen = displayFor(config)
        if not screen then
            cancelPending("display disappeared", true)
            return
        end

        local _, distance, onDisplay = currentDisplayPosition(config, screen)
        if not onDisplay or distance > config.edge + config.cancelDistance then
            cancelPending("mouse left the edge", true)
        end
    end

    local function handleMouse()
        local screen = displayFor(config)
        if not screen then
            lastX = nil
            return false
        end

        local _, distance, onDisplay = currentDisplayPosition(config, screen)
        if not onDisplay then
            lastX = nil
            return false
        end

        local point = hs.mouse.absolutePosition()
        if distance > config.rearm then
            armed = true
        end

        local dx = 0
        if lastX then
            dx = point.x - lastX
        end
        lastX = point.x

        if hs.timer.secondsSinceEpoch() < cooldownUntil or switchInFlight then
            return false
        end

        if armed and not pending and distance <= config.edge and movingTowardEdge(dx) then
            armed = false
            pending = hs.timer.doAfter(config.delay, function()
                stopTimer(pendingMonitor)
                pendingMonitor = nil
                pending = nil

                local latestScreen = displayFor(config)
                if not latestScreen then
                    armed = true
                    return
                end

                local _, latestDistance, latestOnDisplay = currentDisplayPosition(config, latestScreen)
                if latestOnDisplay and latestDistance <= config.edge + config.cancelDistance then
                    startSwitch()
                else
                    armed = true
                    print("display handoff cancelled: mouse did not remain at edge")
                end
            end)
            pendingMonitor = hs.timer.doEvery(0.05, cancelIfMouseMovedBack)
            print("display handoff pending: " .. config.role)
        end

        return false
    end

    local watcher = hs.eventtap.new({
        hs.eventtap.event.types.mouseMoved,
        hs.eventtap.event.types.leftMouseDragged,
        hs.eventtap.event.types.rightMouseDragged
    }, handleMouse)
    watcher:start()

    M.watcher = watcher
    M.status = function()
        return {
            pending = pending ~= nil,
            switchInFlight = switchInFlight,
            armed = armed,
            cooldown = math.max(0, cooldownUntil - hs.timer.secondsSinceEpoch())
        }
    end
end

return M
