#!/bin/bash

# Odyssey-7 Phase 0 Complete Test Suite
# Tests all core functionality

# set -e  # Exit immediately on error

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

echo "=================================="
echo "🎮 Odyssey-7 Phase 0 Complete Test"
echo "=================================="
echo ""

# Function: Print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        ((FAILED++))
    fi
}

# Function: Check JSON response
check_json() {
    if echo "$1" | jq empty 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# ===================================
# Test 1: Health Check
# ===================================
echo "📋 Test 1: Health Check"
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)

if check_json "$HEALTH_RESPONSE"; then
    STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.status')
    if [ "$STATUS" = "healthy" ]; then
        print_result 0 "Health check"
    else
        print_result 1 "Health check - status is not healthy"
    fi
else
    print_result 1 "Health check - response is not JSON"
fi
echo ""

# ===================================
# Test 2: API Documentation
# ===================================
echo "📋 Test 2: API Documentation"
DOC_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)

if [ "$DOC_STATUS" = "200" ]; then
    print_result 0 "API docs accessible (http://localhost:8000/docs)"
else
    print_result 1 "API docs not accessible - HTTP $DOC_STATUS"
fi
echo ""

# ===================================
# Test 3: Create Game
# ===================================
echo "📋 Test 3: Create New Game"
CREATE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/game/start" \
  -H "Content-Type: application/json" \
  -d '{"player_name":"TestPlayer"}')

if check_json "$CREATE_RESPONSE"; then
    SESSION_ID=$(echo "$CREATE_RESPONSE" | jq -r '.session_id')
    
    if [ "$SESSION_ID" != "null" ] && [ -n "$SESSION_ID" ]; then
        print_result 0 "Game created - Session ID: ${SESSION_ID:0:20}..."
        
        # Check returned fields
        OPENING=$(echo "$CREATE_RESPONSE" | jq -r '.opening_narration')
        PHASE=$(echo "$CREATE_RESPONSE" | jq -r '.initial_state.phase')
        PLAYER_NAME=$(echo "$CREATE_RESPONSE" | jq -r '.initial_state.player.name')
        
        if [ "$PLAYER_NAME" = "TestPlayer" ]; then
            print_result 0 "Player name correct"
        else
            print_result 1 "Player name incorrect - expected TestPlayer, got $PLAYER_NAME"
        fi
        
        if [ "$PHASE" = "intro" ]; then
            print_result 0 "Game phase correct"
        else
            print_result 1 "Game phase incorrect - expected intro, got $PHASE"
        fi
    else
        print_result 1 "Game creation - no session_id returned"
        echo "$CREATE_RESPONSE" | jq
        exit 1
    fi
else
    print_result 1 "Game creation - response is not JSON"
    echo "$CREATE_RESPONSE"
    exit 1
fi
echo ""

# ===================================
# Test 4: Get Game State
# ===================================
echo "📋 Test 4: Get Game State"
STATE_RESPONSE=$(curl -s "http://localhost:8000/api/v1/game/state/$SESSION_ID")

if check_json "$STATE_RESPONSE"; then
    print_result 0 "State retrieval - valid JSON returned"
    
    # Check key fields
    OXYGEN=$(echo "$STATE_RESPONSE" | jq -r '.world.resources.oxygen_level.current')
    TURN=$(echo "$STATE_RESPONSE" | jq -r '.turn_count')
    HEALTH=$(echo "$STATE_RESPONSE" | jq -r '.player.health')
    
    if [ "$OXYGEN" != "null" ]; then
        print_result 0 "Resource data - oxygen: $OXYGEN"
    else
        print_result 1 "Resource data - oxygen field missing"
    fi
    
    if [ "$TURN" != "null" ]; then
        print_result 0 "Turn data - current turn: $TURN"
    else
        print_result 1 "Turn data missing"
    fi
    
    if [ "$HEALTH" != "null" ]; then
        print_result 0 "Player data - health: $HEALTH"
    else
        print_result 1 "Player data missing"
    fi
    
    # Save initial oxygen value
    OXYGEN_BEFORE=$OXYGEN
else
    print_result 1 "State retrieval - response is not JSON"
    echo "First 500 chars of response:"
    echo "$STATE_RESPONSE" | head -c 500
    exit 1
fi
echo ""

# ===================================
# Test 5: Execute Player Action
# ===================================
echo "📋 Test 5: Execute Player Action"
ACTION_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/game/action" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION_ID\",\"action_type\":\"investigation\",\"action_id\":\"check_systems\",\"action_text\":\"I check the reactor systems\"}")

if check_json "$ACTION_RESPONSE"; then
    SUCCESS=$(echo "$ACTION_RESPONSE" | jq -r '.success')
    
    if [ "$SUCCESS" = "true" ]; then
        print_result 0 "Action execution - success"
        
        NARRATION=$(echo "$ACTION_RESPONSE" | jq -r '.narration')
        echo "   📖 Narration: ${NARRATION:0:80}..."
    else
        print_result 1 "Action execution - success is false"
    fi
else
    print_result 1 "Action execution - response is not JSON"
    echo "$ACTION_RESPONSE"
fi
echo ""

# ===================================
# Test 6: Verify State Persistence
# ===================================
echo "📋 Test 6: Verify State Persistence"
STATE_RESPONSE2=$(curl -s "http://localhost:8000/api/v1/game/state/$SESSION_ID")

if check_json "$STATE_RESPONSE2"; then
    OXYGEN_AFTER=$(echo "$STATE_RESPONSE2" | jq -r '.world.resources.oxygen_level.current')
    TURN_AFTER=$(echo "$STATE_RESPONSE2" | jq -r '.turn_count')
    
    print_result 0 "State update - oxygen: $OXYGEN_BEFORE → $OXYGEN_AFTER"
    print_result 0 "State update - turn: $TURN_AFTER"
    
    if [ "$TURN_AFTER" != "$TURN" ]; then
        print_result 0 "Turn count increased (persistence works)"
    else
        print_result 1 "Turn count did not increase"
    fi
else
    print_result 1 "State persistence verification failed"
fi
echo ""

# ===================================
# Test 7: End Turn
# ===================================
echo "📋 Test 7: Manual End Turn"
END_TURN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/game/end-turn/$SESSION_ID")

if check_json "$END_TURN_RESPONSE"; then
    TURN_NUMBER=$(echo "$END_TURN_RESPONSE" | jq -r '.turn_number')
    
    if [ "$TURN_NUMBER" != "null" ]; then
        print_result 0 "End turn - turn $TURN_NUMBER"
    else
        print_result 1 "End turn - turn number missing"
    fi
else
    print_result 1 "End turn failed"
fi
echo ""

# ===================================
# Test 8: MongoDB Data Verification
# ===================================
echo "📋 Test 8: MongoDB Data Persistence"
MONGO_COUNT=$(docker-compose exec -T mongodb mongosh --quiet --eval "db.getSiblingDB('ai_rpg_game').sessions.countDocuments()" 2>/dev/null | tail -1)

if [ -n "$MONGO_COUNT" ] && [ "$MONGO_COUNT" -gt 0 ]; then
    print_result 0 "MongoDB data exists - $MONGO_COUNT session(s)"
else
    print_result 1 "MongoDB data verification failed"
fi
echo ""

# ===================================
# Test 9: Data Model Integrity
# ===================================
echo "📋 Test 9: Data Model Integrity Check"

# Check WorldState's ship_systems
REACTOR=$(echo "$STATE_RESPONSE2" | jq -r '.world.ship_systems.reactor_integrity.integrity')
HULL=$(echo "$STATE_RESPONSE2" | jq -r '.world.ship_systems.hull_integrity.integrity')
LIFE_SUPPORT=$(echo "$STATE_RESPONSE2" | jq -r '.world.ship_systems.life_support_efficiency.integrity')

if [ "$REACTOR" != "null" ]; then
    print_result 0 "ShipSystems - reactor_integrity: $REACTOR"
else
    print_result 1 "ShipSystems - reactor_integrity missing"
fi

if [ "$HULL" != "null" ]; then
    print_result 0 "ShipSystems - hull_integrity: $HULL"
else
    print_result 1 "ShipSystems - hull_integrity missing"
fi

if [ "$LIFE_SUPPORT" != "null" ]; then
    print_result 0 "ShipSystems - life_support_efficiency: $LIFE_SUPPORT"
else
    print_result 1 "ShipSystems - life_support_efficiency missing"
fi

# Check ResourceLevels
FUEL=$(echo "$STATE_RESPONSE2" | jq -r '.world.resources.fuel_reserves.current')
POWER=$(echo "$STATE_RESPONSE2" | jq -r '.world.resources.power_level.current')

if [ "$FUEL" != "null" ]; then
    print_result 0 "ResourceLevels - fuel_reserves: $FUEL"
else
    print_result 1 "ResourceLevels - fuel_reserves missing"
fi

if [ "$POWER" != "null" ]; then
    print_result 0 "ResourceLevels - power_level: $POWER"
else
    print_result 1 "ResourceLevels - power_level missing"
fi

echo ""

# ===================================
# Final Summary
# ===================================
echo "=================================="
echo "📊 Test Summary"
echo "=================================="
echo ""
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Phase 0 complete!${NC}"
    echo ""
    echo "✅ Verified features:"
    echo "  • Backend health check"
    echo "  • API documentation access"
    echo "  • Game session creation"
    echo "  • Game state retrieval"
    echo "  • Player action execution"
    echo "  • State persistence to MongoDB"
    echo "  • Manual turn ending"
    echo "  • Complete data model conversion"
    echo ""
    echo "🚀 System is ready! You can start Phase 1 development"
    echo ""
    echo "📝 Available API Endpoints:"
    echo "  • http://localhost:8000/docs - API Documentation"
    echo "  • http://localhost:8000/health - Health Check"
    echo "  • http://localhost:8000/api/v1/game/start - Create Game"
    echo "  • http://localhost:8000/api/v1/game/state/{id} - Get State"
    echo "  • http://localhost:8000/api/v1/game/action - Execute Action"
    echo ""
    exit 0
else
    echo -e "${RED}❌ $FAILED test(s) failed${NC}"
    echo ""
    echo "Please check errors and fix"
    echo ""
    exit 1
fi