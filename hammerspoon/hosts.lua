local home = os.getenv("HOME")
local localConfig = {}
local localConfigPath = home .. "/.hammerspoon-local.lua"
local ok, result = pcall(dofile, localConfigPath)
if ok and type(result) == "table" then
    localConfig = result
end

local common = {
    ddc = "/opt/homebrew/bin/m1ddc",
    displayName = "DELL S2721Q",
    edge = 4,
    rearm = 80,
    cancelDistance = 24,
    delay = 0.45,
    controllerPort = 48532,
    controllerToken = localConfig.presenceToken,
    allowedInputs = { ["15"] = true, ["17"] = true }
}

local function merge(base, extra)
    local result = {}
    for key, value in pairs(base) do
        result[key] = value
    end
    for key, value in pairs(extra or {}) do
        result[key] = value
    end
    return result
end

return {
    mbp = {
        handoff = merge(common, {
            role = "mbp",
            displayUUID = "C10DADDE-9DE3-45BB-AF23-FFAFDC449029",
            activeInput = "15",
            targetInput = "17",
            targetLabel = "HDMI1",
            controllerRole = "client",
            controllerHost = "192.168.233.12"
        }),
        presence = {
            role = "sender",
            miniHost = "192.168.233.12",
            port = 48531,
            token = localConfig.presenceToken,
            interval = 5
        }
    },

    m4mini = {
        handoff = merge(common, {
            role = "m4mini",
            displayUUID = "8AEB4384-2FA7-459D-AA4D-41A9613049E3",
            activeInput = "17",
            targetInput = "15",
            targetLabel = "DisplayPort",
            controllerRole = "server"
        }),
        presence = {
            role = "receiver",
            port = 48531,
            token = localConfig.presenceToken,
            absenceTimeout = 35,
            startupGrace = 45
        }
    }
}
