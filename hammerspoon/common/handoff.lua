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
    -- m1ddc 在 Ghostty 中同步执行正常；这里也走同一条路径，避免
    -- hs.task 的异步回调在 Universal Control 切屏时卡住状态机。
    local command = string.format(
        "%q display %q set input %q",
        config.ddc,
        config.displayUUID,
        config.targetInput
    )
    local output, ok, _, exitCode = hs.execute(command)
    if not ok then
        print(string.format(
            "display handoff failed: exit=%s output=%s",
            tostring(exitCode), output or ""
        ))
    end
    done(ok == true, output or "")
end

local function readInput(config, done)
    local command = string.format(
        "%q display %q get input",
        config.ddc,
        config.displayUUID
    )
    local output, ok = hs.execute(command)
    if ok then
        done(tonumber((output or ""):match("%d+")), output or "")
    else
        done(nil, output or "")
    end
end

function M.start(config)
    local armed = false
    local lastX = nil
    local pending = nil
    local pendingMonitor = nil
    local settleTimer = nil
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

    local function reconcileInput()
        settleTimer = nil
        if switchInFlight or hs.timer.secondsSinceEpoch() < cooldownUntil then
            return
        end

        readInput(config, function(input)
            if input == nil or input == tonumber(config.targetInput) then
                return
            end
            print(string.format(
                "display handoff reconcile: current=%s target=%s role=%s",
                tostring(input), config.targetInput, config.role
            ))
            startSwitch()
        end)
    end

    local function scheduleReconcile()
        stopTimer(settleTimer)
        settleTimer = hs.timer.doAfter(config.settleDelay, reconcileInput)
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
        -- Universal Control can move the pointer to MBP before the mini-side
        -- eventtap sees the final event. Keep that intent alive across the
        -- boundary; a reversal back into the mini still cancels it.
        if (onDisplay and distance > config.edge + config.cancelDistance)
            or (config.role ~= "m4mini" and not onDisplay) then
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
        -- Universal Control may return the pointer to this Mac without
        -- touching this display's edge again. Once the pointer settles on
        -- this host, converge the DDC input to this host's target.
        scheduleReconcile()
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

                local latestPoint, latestDistance, latestOnDisplay = currentDisplayPosition(config, latestScreen)
                local latestFrame = latestScreen:fullFrame()
                local crossedFromMini = config.role == "m4mini"
                    and latestPoint.x >= latestFrame.x + latestFrame.w
                        - config.edge - config.cancelDistance
                    and (latestOnDisplay or latestPoint.x > latestFrame.x + latestFrame.w)
                local stayedOnMBP = config.role == "mbp"
                    and latestOnDisplay
                    and latestDistance <= config.edge + config.cancelDistance
                if crossedFromMini or stayedOnMBP then
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
            reconcilePending = settleTimer ~= nil,
            switchInFlight = switchInFlight,
            armed = armed,
            cooldown = math.max(0, cooldownUntil - hs.timer.secondsSinceEpoch())
        }
    end
end

return M
