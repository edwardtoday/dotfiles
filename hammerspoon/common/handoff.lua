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
    local initialControllerStatus = controller.status()
    local observedControllerInput = initialControllerStatus.currentInput
    local observedControllerRevision = initialControllerStatus.revision
    local reversalUntil = 0
    local reversalTravel = 0
    local reversalRequests = 0

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
        local rawDx = event:getProperty(hs.eventtap.event.properties.mouseEventDeltaX) or 0
        local now = hs.timer.secondsSinceEpoch()

        -- 物理鼠标连接在 MBP。请求 HDMI 后的短窗口内，直接根据原始
        -- 向右增量识别“黑屏期间立即回 MBP”，不依赖 UC 映射坐标。
        if config.reversalTargetInput and now < reversalUntil then
            if rawDx > 0 then
                reversalTravel = reversalTravel + rawDx
                if reversalTravel >= config.cancelDistance then
                    reversalUntil = 0
                    reversalTravel = 0
                    reversalRequests = reversalRequests + 1
                    controller.request(config.reversalTargetInput)
                    print("display handoff immediate reversal: " .. config.reversalTargetInput)
                    return false
                end
            elseif rawDx < 0 then
                reversalTravel = 0
            end
        elseif reversalUntil ~= 0 then
            reversalUntil = 0
            reversalTravel = 0
        end

        local controllerStatus = controller.status()
        local controllerInput = controllerStatus.currentInput
        local controllerChanged = controllerStatus.revision ~= nil
            and controllerStatus.revision ~= observedControllerRevision
        if controllerChanged then
            observedControllerRevision = controllerStatus.revision
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

        if rawDx == 0 then
            rawDx = absoluteDx
        end

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
                if config.reversalTargetInput then
                    reversalUntil = lastSwitchAt + config.reversalWindow
                    reversalTravel = 0
                end
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
            observedControllerRevision = observedControllerRevision,
            reverseDistance = reverseDistance,
            reversalRemaining = math.max(0, reversalUntil - hs.timer.secondsSinceEpoch()),
            reversalTravel = reversalTravel,
            reversalRequests = reversalRequests,
            switchAttempts = switchAttempts,
            lastSwitchAt = lastSwitchAt
        }
    end
end

return M
