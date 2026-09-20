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

    if config.controllerRole == "server" then
        local statePath = os.getenv("HOME") .. "/Library/Caches/Hammerspoon/display-input.state"
        local currentInput = loadState(statePath)

        local function apply(targetInput)
            requests = requests + 1
            lastTarget = targetInput
            if currentInput == targetInput then
                skipped = skipped + 1
                print("display input unchanged: " .. targetInput)
                return true
            end

            print(string.format("display input apply: %s", targetInput))
            if not runDDC(config, targetInput) then
                return false
            end

            currentInput = targetInput
            saveState(statePath, currentInput)
            switches = switches + 1
            return true
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
        M.status = function()
            return {
                role = config.controllerRole,
                currentInput = currentInput,
                requests = requests,
                switches = switches,
                skipped = skipped,
                lastTarget = lastTarget
            }
        end
        return
    end

    local socket = hs.socket.udp.new()
    local retryTimer = nil

    M.socket = socket
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
