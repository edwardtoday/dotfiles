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
    local reverseDistance = 0
    local switchAttempts = 0
    local lastSwitchAt = nil
    local observedControllerInput = controller.status().currentInput

    local movingTowardEdge = config.role == "mbp" and function(dx)
        return dx < 0
    end or function(dx)
        return dx > 0
    end
    local movingBack = config.role == "mbp" and function(dx)
        return dx > 0
    end or function(dx)
        return dx < 0
    end

    local function cancelPending(reason, rearm)
        stopTimer(pending)
        pending = nil
        reverseDistance = 0
        if rearm then
            armed = true
        end
        print("display handoff cancelled: " .. reason)
    end

    local function sourceIsActive()
        local active = controller.isCurrent(config.activeInput)
        return active == nil or active == true
    end

    local function handleMouse(event)
        local controllerInput = controller.status().currentInput
        if controllerInput ~= nil and controllerInput ~= observedControllerInput then
            observedControllerInput = controllerInput
            if controllerInput == config.activeInput then
                -- 显示器刚切到本机时允许立即反向，不要求先深入屏幕再重置。
                armed = true
                print("display handoff armed on input activation: " .. controllerInput)
            end
        end

        if not sourceIsActive() then
            if pending then
                cancelPending("source input is inactive", false)
            end
            armed = false
            lastX = nil
            return false
        end

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

        local absoluteDx = 0
        if lastX then
            absoluteDx = point.x - lastX
        end
        lastX = point.x

        local rawDx = event:getProperty(hs.eventtap.event.properties.mouseEventDeltaX) or absoluteDx

        if pending then
            if movingBack(rawDx) then
                reverseDistance = reverseDistance + math.abs(rawDx)
                if reverseDistance >= config.cancelDistance then
                    cancelPending("mouse moved back", true)
                end
            elseif movingTowardEdge(rawDx) then
                reverseDistance = 0
            end
            return false
        end

        if distance > config.rearm then
            armed = true
        end

        if armed and distance <= config.edge and movingTowardEdge(rawDx) then
            armed = false
            reverseDistance = 0
            pending = hs.timer.doAfter(config.delay, function()
                pending = nil
                reverseDistance = 0
                switchAttempts = switchAttempts + 1
                lastSwitchAt = hs.timer.secondsSinceEpoch()
                controller.request(config.targetInput)
                print(string.format(
                    "display handoff requested: %s -> %s (%s)",
                    config.role, config.targetLabel, config.targetInput
                ))
            end)
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
            sourceActive = sourceIsActive(),
            observedControllerInput = observedControllerInput,
            reverseDistance = reverseDistance,
            switchAttempts = switchAttempts,
            lastSwitchAt = lastSwitchAt
        }
    end
end

return M
