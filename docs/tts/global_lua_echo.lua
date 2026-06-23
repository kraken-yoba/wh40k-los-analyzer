-- Phase 1 TTS bridge harness for a controlled local development save.
-- Paste into the Global script. Keep raw saves and captured output outside git.
-- This script sends JSON through WebRequest.custom to the local Python companion.

local COMPANION_BASE_URL = "http://127.0.0.1:8000"
local HEALTH_URL = COMPANION_BASE_URL .. "/api/tts/health"
local SNAPSHOT_URL = COMPANION_BASE_URL .. "/api/tts/snapshot"
local REQUEST_TIMEOUT_SECONDS = 5

local TAG_ATTACKER = "tts-attacker"
local TAG_TARGET = "tts-target"
local TAG_TERRAIN = "tts-terrain"

local BOARD_TRANSFORM = {
    schema_version = "tts-board-transform/v0",
    tts_origin = {x = 0.0, y = 0.0, z = 0.0},
    battlefield_origin = {x = 0.0, y = 0.0},
    board_rotation_degrees_clockwise = 0.0,
    tts_units_per_inch = 1.0,
    board_width_inches = 44.0,
    board_height_inches = 60.0,
    round_trip_tolerance_inches = 0.25,
    calibration_points = {
        {
            label = "lower-left",
            world = {x = 0.0, y = 0.0, z = 0.0},
            battlefield = {x = 0.0, y = 0.0},
        },
        {
            label = "upper-right",
            world = {x = 44.0, y = 0.0, z = 60.0},
            battlefield = {x = 44.0, y = 60.0},
        },
    },
}

function onLoad()
    print("Warhammer companion Phase 1 TTS bridge harness loaded.")
    print("Run ttsHealth() or ttsSendSnapshot() from the TTS scripting console.")
end

function ttsHealth()
    sendJson("GET", HEALTH_URL, nil, function(response)
        print("TTS bridge health response: " .. response)
    end)
end

function ttsSendSnapshot()
    local attacker = findTaggedObject(TAG_ATTACKER)
    local target = findTaggedObject(TAG_TARGET)
    local terrain = findTaggedObject(TAG_TERRAIN)

    if attacker == nil or target == nil or terrain == nil then
        broadcastToAll("TTS bridge snapshot blocked: tag attacker, target, and terrain first.", {1, 0.3, 0.3})
        return
    end

    local los = buildDiagnosticLosProbe(attacker, target)
    local snapshot = {
        schema_version = "tts-board-snapshot/v0",
        snapshot_id = "local-tts-phase-1",
        captured_at_epoch = os.time(),
        source = "local controlled TTS save",
        host_context = {
            schema_version = "tts-host-context/v0",
            host_only = true,
            local_companion_required = true,
            live_tts_round_trip_observed = true,
            note = "127.0.0.1 resolves on the TTS host machine.",
        },
        transform = BOARD_TRANSFORM,
        objects = {
            objectRef(attacker, "attacker", TAG_ATTACKER),
            objectRef(target, "target", TAG_TARGET),
            objectRef(terrain, "terrain", TAG_TERRAIN),
        },
        diagnostic_los = los,
    }

    sendJson("POST", SNAPSHOT_URL, snapshot, function(response)
        print("TTS bridge snapshot response: " .. response)
    end)
end

function sendJson(method, url, payload, callback)
    local body = ""
    if payload ~= nil then
        body = JSON.encode(payload)
    end

    local headers = {
        ["Content-Type"] = "application/json",
        Accept = "application/json",
    }
    local completed = false

    Wait.time(function()
        if not completed then
            completed = true
            broadcastToAll("TTS bridge request timed out locally: " .. method .. " " .. url, {1, 0.6, 0.2})
        end
    end, REQUEST_TIMEOUT_SECONDS)

    WebRequest.custom(url, method, true, body, headers, function(request)
        if completed then
            return
        end
        completed = true

        if request.is_error then
            broadcastToAll("TTS bridge request failed: " .. tostring(request.error), {1, 0.3, 0.3})
            return
        end

        if request.response_code < 200 or request.response_code >= 300 then
            broadcastToAll("TTS bridge rejected status: " .. tostring(request.response_code), {1, 0.6, 0.2})
            print(request.text)
            return
        end

        callback(request.text)
    end)
end

function findTaggedObject(tag)
    for _, object in ipairs(getAllObjects()) do
        if object.hasTag ~= nil and object.hasTag(tag) then
            return object
        end
    end
    return nil
end

function objectRef(object, kind, tag)
    return {
        guid = object.getGUID(),
        name = object.getName(),
        object_kind = kind,
        tags = {tag},
        position = object.getPosition(),
        rotation = object.getRotation(),
        scale = object.getScale(),
        provenance = "tagged",
    }
end

function buildDiagnosticLosProbe(attacker, target)
    local startPosition = attacker.getPosition()
    local endPosition = target.getPosition()
    startPosition.y = startPosition.y + 1.0
    endPosition.y = endPosition.y + 1.0

    local direction, distance = directionAndDistance(startPosition, endPosition)
    local hits = Physics.cast({
        origin = startPosition,
        direction = direction,
        type = 1,
        max_distance = distance,
        debug = true,
    })

    local hit = false
    local hitGuid = nil
    if #hits > 0 and hits[1].hit_object ~= nil then
        hit = true
        hitGuid = hits[1].hit_object.getGUID()
        markDiagnosticHit(hits[1].point)
    end

    return {
        schema_version = "tts-diagnostic-los-probe/v0",
        probe_id = "local-diagnostic-physics-cast",
        source_guid = attacker.getGUID(),
        target_guid = target.getGUID(),
        start_world = startPosition,
        end_world = endPosition,
        hit = hit,
        hit_guid = hitGuid,
        authoritative = false,
        label = "Diagnostic physics cast, not gameplay LOS",
    }
end

function directionAndDistance(startPosition, endPosition)
    local dx = endPosition.x - startPosition.x
    local dy = endPosition.y - startPosition.y
    local dz = endPosition.z - startPosition.z
    local distance = math.sqrt((dx * dx) + (dy * dy) + (dz * dz))
    if distance <= 0 then
        return {x = 0, y = 1, z = 0}, 0
    end
    return {x = dx / distance, y = dy / distance, z = dz / distance}, distance
end

function markDiagnosticHit(point)
    broadcastToAll(
        "Diagnostic hit marker at x=" .. round(point.x) .. ", y=" .. round(point.y) .. ", z=" .. round(point.z),
        {1, 0.9, 0.2}
    )
end

function round(value)
    return tostring(math.floor((value * 100) + 0.5) / 100)
end
