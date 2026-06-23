-- Phase 1 TTS External Editor proof probe.
-- This file is executed transiently through TTS's External Editor API.
-- It must not be saved into a user save or used with Save & Play.

local COMPANION_BASE_URL = "__COMPANION_BASE_URL__"
local RECEIPT = "__RECEIPT__"
local URL = COMPANION_BASE_URL .. "/api/tts/health?receipt=" .. RECEIPT

WebRequest.custom(URL, "GET", true, "", {
    ["Content-Type"] = "application/json",
    Accept = "application/json",
}, function(request)
    local status = "unknown"
    if request ~= nil and request.response_code ~= nil then
        status = tostring(request.response_code)
    end
    print("Warhammer companion TTS proof receipt " .. RECEIPT .. " status " .. status)
end)
