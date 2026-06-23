-- Phase 1 operator-assisted TTS Lua health receipt proof.
-- Prefer the first System Console command printed by tts-manual-health.
-- Use this snippet only in a real Lua execution surface for a controlled local table.
-- The script sends one GET request to the runner-owned local proof server.

local COMPANION_BASE_URL = "__COMPANION_BASE_URL__"
local RECEIPT = "__RECEIPT__"
local URL = COMPANION_BASE_URL .. "/api/tts/health?receipt=" .. RECEIPT

WebRequest.custom(URL, "GET", true, "", {
    ["Content-Type"] = "application/json",
    Accept = "application/json",
    ["X-Warhammer-TTS-Proof"] = RECEIPT,
}, function(request)
    if request.is_error then
        print("Warhammer companion manual proof failed: " .. tostring(request.error))
        return
    end
    print("Warhammer companion manual proof status: " .. tostring(request.response_code))
end)
