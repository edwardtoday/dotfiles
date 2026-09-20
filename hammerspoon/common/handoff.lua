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

function M.start(config)
    local stateDir = os.getenv("HOME") .. "/Library/Caches/Hammerspoon"
    local statePath = stateDir .. "/display-handoff-" .. config.role .. ".state"

    local function loadAssumedInput()
        local file = io.open(statePath, "r")
        if not file then
            return nil
        end
        local value = tonumber(file:read("*l"))
        file:close()
        return value
    end

    local function saveAssumedInput(value)
        hs.fs.mkdir(stateDir)
        local temporaryPath = statePath .. ".tmp"
        local file = io.open(temporaryPath, "w")
        if not file then
            return false
        end
        file:write(tostring(value), "\n")
        file:close()
        return os.rename(temporaryPath, statePath) == true
    end

    local function clearAssumedInput()
        os.remove(statePath)
    end

    local armed = false
    local lastX = nil
    local pending = nil
    local pendingMonitor = nil
    local settleTimer = nil
    local switchInFlight = false
    local cooldownUntil = 0
    local switchAttempts = 0
    local switchSuccesses = 0
    local lastSwitchAt = nil
    local peerInvalidations = 0
    -- m1ddc 1.2.0 的 `get input` 回读值不稳定，不能用它判断是否需要
    -- 重复 set。记录本进程最近一次成功设置的目标，避免周期性黑屏。
    local assumedInput = loadAssumedInput()
    local stateSocket = hs.socket.udp.new()

    local movingTowardEdge = config.role == "mbp" and function(dx)
        return dx < 0
    end or function(dx)
        return dx > 0
    end

    local function markDeparted()
        stopTimer(settleTimer)
        settleTimer = nil
        assumedInput = nil
        clearAssumedInput()
    end

    local statePrefix = config.stateToken .. "|"
    local stateServer = hs.socket.udp.server(config.statePort, function(data)
        local peerRole = nil
        if data and data:sub(1, #statePrefix) == statePrefix then
            peerRole = data:sub(#statePrefix + 1)
        end
        if peerRole and peerRole ~= config.role then
            peerInvalidations = peerInvalidations + 1
            markDeparted()
            print("display handoff peer changed input: " .. peerRole)
        end
    end)
    stateServer:receive()

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
        if assumedInput == tonumber(config.targetInput) then
            switchInFlight = false
            return
        end

        switchAttempts = switchAttempts + 1
        runDDC(config, function(ok)
            switchInFlight = false
            if ok then
                assumedInput = tonumber(config.targetInput)
                saveAssumedInput(assumedInput)
                switchSuccesses = switchSuccesses + 1
                lastSwitchAt = hs.timer.secondsSinceEpoch()
                cooldownUntil = hs.timer.secondsSinceEpoch() + config.cooldown
                stateSocket:send(
                    config.stateToken .. "|" .. config.role,
                    config.peerHost,
                    config.statePort
                )
                print(string.format("display handoff applied: input=%s", config.targetInput))
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

        if assumedInput == tonumber(config.targetInput) then
            return
        end
        print(string.format(
            "display handoff reconcile: target=%s role=%s",
            config.targetInput, config.role
        ))
        startSwitch()
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
            if not onDisplay then
                markDeparted()
            end
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
            markDeparted()
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
                if crossedFromMini then
                    markDeparted()
                    print("display handoff departed: m4mini")
                elseif stayedOnMBP then
                    -- 光标仍停在边缘，等待目的机器实际收到鼠标事件后再切换。
                    print("display handoff waiting at edge: mbp")
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
    M.stateServer = stateServer
    M.stateSocket = stateSocket
    M.status = function()
        return {
            pending = pending ~= nil,
            reconcilePending = settleTimer ~= nil,
            switchInFlight = switchInFlight,
            armed = armed,
            cooldown = math.max(0, cooldownUntil - hs.timer.secondsSinceEpoch()),
            assumedInput = assumedInput,
            switchAttempts = switchAttempts,
            switchSuccesses = switchSuccesses,
            lastSwitchAt = lastSwitchAt,
            peerInvalidations = peerInvalidations
        }
    end
end

return M
