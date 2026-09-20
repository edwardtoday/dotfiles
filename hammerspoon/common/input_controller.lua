local M = {}

local function saveState(path, value)
    local directory = path:match("^(.*)/[^/]+$")
    if directory then
        hs.fs.mkdir(directory)
    end
    local temporary = path .. ".tmp"
    local file = io.open(temporary, "w")
    if not file then
        return false
    end
    file:write(tostring(value), "\n")
    file:close()
    return os.rename(temporary, path) == true
end

local function loadState(path)
    local file = io.open(path, "r")
    if not file then
        return nil
    end
    local value = file:read("*l")
    file:close()
    return value
end

local function runDDC(config, targetInput)
    local command = string.format(
        "%q display %q set input %q",
        config.ddc,
        config.displayUUID,
        targetInput
    )
    local output, ok, _, exitCode = hs.execute(command)
    if not ok then
        print(string.format(
            "display input failed: exit=%s output=%s",
            tostring(exitCode), output or ""
        ))
    end
    return ok == true
end

function M.start(config)
    if M.started then
        return
    end
    M.started = true

    local requests = 0
    local switches = 0
    local skipped = 0
    local lastTarget = nil
    local revision = 0

    if config.controllerRole == "server" then
        local statePath = os.getenv("HOME") .. "/Library/Caches/Hammerspoon/display-input.state"
        local currentInput = loadState(statePath)
        local desiredInput = nil
        local retryTimer = nil
        local retryCount = 0
        local failedAttempts = 0

        local attemptApply
        attemptApply = function()
            if not desiredInput then
                return true
            end

            local targetInput = desiredInput
            if currentInput == targetInput then
                skipped = skipped + 1
                desiredInput = nil
                retryCount = 0
                print("display input unchanged: " .. targetInput)
                return true
            end

            print(string.format(
                "display input apply: %s attempt=%s",
                targetInput, tostring(retryCount + 1)
            ))
            if runDDC(config, targetInput) then
                currentInput = targetInput
                saveState(statePath, currentInput)
                switches = switches + 1
                revision = revision + 1
                desiredInput = nil
                retryCount = 0
                return true
            end

            failedAttempts = failedAttempts + 1
            retryCount = retryCount + 1
            if retryCount < config.controllerMaxAttempts then
                retryTimer = hs.timer.doAfter(config.controllerRetryDelay, function()
                    retryTimer = nil
                    attemptApply()
                end)
            else
                print("display input retry exhausted: " .. targetInput)
                desiredInput = nil
                retryCount = 0
            end
            return false
        end

        local function apply(targetInput)
            requests = requests + 1
            lastTarget = targetInput
            if retryTimer then
                retryTimer:stop()
                retryTimer = nil
            end
            if desiredInput ~= targetInput then
                retryCount = 0
            end
            desiredInput = targetInput
            return attemptApply()
        end

        local prefix = config.controllerToken .. "|"
        local server = hs.socket.udp.server(config.controllerPort, function(data)
            if not data or data:sub(1, #prefix) ~= prefix then
                return
            end
            local targetInput = data:sub(#prefix + 1)
            if not config.allowedInputs[targetInput] then
                return
            end
            apply(targetInput)
        end)
        server:receive()

        M.server = server
        M.request = apply
        M.isCurrent = function(input)
            return currentInput == input
        end
        M.status = function()
            return {
                role = config.controllerRole,
                currentInput = currentInput,
                desiredInput = desiredInput,
                requests = requests,
                switches = switches,
                skipped = skipped,
                lastTarget = lastTarget,
                revision = revision,
                retryPending = retryTimer ~= nil,
                retryCount = retryCount,
                failedAttempts = failedAttempts
            }
        end
        return
    end

    local socket = hs.socket.udp.new()
    local retryTimer = nil

    M.socket = socket
    M.isCurrent = function()
        return nil
    end
    M.request = function(targetInput)
        requests = requests + 1
        lastTarget = targetInput
        local payload = config.controllerToken .. "|" .. targetInput
        socket:send(payload, config.controllerHost, config.controllerPort)
        if retryTimer then
            retryTimer:stop()
        end
        retryTimer = hs.timer.doAfter(0.12, function()
            retryTimer = nil
            socket:send(payload, config.controllerHost, config.controllerPort)
        end)
        return true
    end
    M.status = function()
        return {
            role = config.controllerRole,
            requests = requests,
            lastTarget = lastTarget,
            retryPending = retryTimer ~= nil
        }
    end
end

return M
