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

function M.start(config)
    local controller = require("input_controller")
    controller.start(config)

    local armed = false
    local lastX = nil
    local pending = nil
    local pendingMonitor = nil
    local switchAttempts = 0
    local lastSwitchAt = nil

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
        if onDisplay and distance > config.edge + config.cancelDistance then
            cancelPending("mouse moved back", true)
        end
    end

    local function handleMouse()
        local screen = displayFor(config)
        if not screen then
            lastX = nil
            return false
        end

        local point, distance, onDisplay = currentDisplayPosition(config, screen)
        if not onDisplay then
            lastX = nil
            return false
        end

        if distance > config.rearm then
            armed = true
        end

        local dx = 0
        if lastX then
            dx = point.x - lastX
        end
        lastX = point.x

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
                if latestOnDisplay and latestDistance > config.edge + config.cancelDistance then
                    armed = true
                    print("display handoff cancelled: mouse did not cross edge")
                    return
                end

                switchAttempts = switchAttempts + 1
                lastSwitchAt = hs.timer.secondsSinceEpoch()
                controller.request(config.targetInput)
                print(string.format(
                    "display handoff requested: %s -> %s (%s)",
                    config.role, config.targetLabel, config.targetInput
                ))
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
            armed = armed,
            switchAttempts = switchAttempts,
            lastSwitchAt = lastSwitchAt
        }
    end
end

return M
