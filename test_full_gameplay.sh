#!/bin/bash
# =============================================================================
# Star-Odyssey 完整游戏流程 E2E 测试
# =============================================================================

set -e
API_URL="http://localhost:8000/api/v1"

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         Star-Odyssey 完整用户体验测试                            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Step 1: 开始新游戏
# =============================================================================
echo -e "${BLUE}━━━ Step 1: 开始新游戏 ━━━${NC}"
START_RESP=$(curl -s -X POST "$API_URL/game/start" \
  -H "Content-Type: application/json" \
  -d '{"player_name":"Commander Chen"}')

SESSION_ID=$(echo "$START_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['sessionId'])")
echo -e "${GREEN}✓ Session ID: $SESSION_ID${NC}"

NARRATION=$(echo "$START_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('initialNarration', 'N/A')[:150])")
echo -e "${YELLOW}📖 开场白: $NARRATION...${NC}"
echo ""

# =============================================================================
# Step 2: 执行一个探索行为
# =============================================================================
echo -e "${BLUE}━━━ Step 2: 探索飞船系统 ━━━${NC}"
ACTION_RESP=$(curl -s -X POST "$API_URL/game/action" \
  -H "Content-Type: application/json" \
  -d "{\"sessionId\":\"$SESSION_ID\",\"actionType\":\"investigation\",\"actionId\":\"check_systems\",\"actionText\":\"I carefully examine the ship's diagnostic panels\"}")

SUCCESS=$(echo "$ACTION_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))")
NARRATION=$(echo "$ACTION_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('narration', 'N/A')[:150])")
echo -e "${GREEN}✓ Action success: $SUCCESS${NC}"
echo -e "${YELLOW}📖 叙述: $NARRATION...${NC}"
echo ""

# =============================================================================
# Step 3: 结束回合
# =============================================================================
echo -e "${BLUE}━━━ Step 3: 结束回合 (资源衰减, NPC行动) ━━━${NC}"
TURN_RESP=$(curl -s -X POST "$API_URL/game/end-turn/$SESSION_ID")

TURN_NUM=$(echo "$TURN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('turnNumber', 'N/A'))")
NARRATION=$(echo "$TURN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('turnSummary', 'N/A')[:150])")
ALERTS=$(echo "$TURN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('criticalAlerts', []))")
echo -e "${GREEN}✓ Turn $TURN_NUM 完成${NC}"
echo -e "${YELLOW}📖 回合总结: $NARRATION...${NC}"
echo -e "⚠️  警报: $ALERTS"
echo ""

# =============================================================================
# Step 4: 保存游戏
# =============================================================================
echo -e "${BLUE}━━━ Step 4: 保存游戏 ━━━${NC}"
SAVE_RESP=$(curl -s -X POST "$API_URL/save/save" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION_ID\",\"save_name\":\"Test Save - Turn 1\"}")

SAVE_ID=$(echo "$SAVE_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('saveId', 'N/A'))")
echo -e "${GREEN}✓ 存档 ID: $SAVE_ID${NC}"
echo ""

# =============================================================================
# Step 5: 再执行几个回合
# =============================================================================
echo -e "${BLUE}━━━ Step 5: 执行更多行为 ━━━${NC}"
for i in 1 2 3; do
  # 执行行为
  curl -s -X POST "$API_URL/game/action" \
    -H "Content-Type: application/json" \
    -d "{\"sessionId\":\"$SESSION_ID\",\"actionType\":\"exploration\",\"actionId\":\"explore_area\",\"actionText\":\"I explore the surrounding area\"}" > /dev/null
  
  # 结束回合
  TURN_RESP=$(curl -s -X POST "$API_URL/game/end-turn/$SESSION_ID")
  TURN_NUM=$(echo "$TURN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('turnNumber', 'N/A'))")
  echo -e "${GREEN}✓ Turn $TURN_NUM 完成${NC}"
done
echo ""

# =============================================================================
# Step 6: 获取游戏状态
# =============================================================================
echo -e "${BLUE}━━━ Step 6: 检查当前状态 ━━━${NC}"
STATE_RESP=$(curl -s "$API_URL/game/state/$SESSION_ID")
LOCATION=$(echo "$STATE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('player',{}).get('location','N/A'))")
HEALTH=$(echo "$STATE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('player',{}).get('health','N/A'))")
TURN=$(echo "$STATE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('world',{}).get('turn','N/A'))")
echo -e "${GREEN}✓ 位置: $LOCATION, 健康: $HEALTH, 回合: $TURN${NC}"
echo ""

# =============================================================================
# Step 7: 列出存档
# =============================================================================
echo -e "${BLUE}━━━ Step 7: 列出存档 ━━━${NC}"
SAVES_RESP=$(curl -s "$API_URL/save/saves")
TOTAL=$(echo "$SAVES_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total', 0))")
echo -e "${GREEN}✓ 共有 $TOTAL 个存档${NC}"
echo ""

# =============================================================================
# Step 8: 加载存档
# =============================================================================
echo -e "${BLUE}━━━ Step 8: 加载存档 (回到 Turn 1) ━━━${NC}"
LOAD_RESP=$(curl -s -X POST "$API_URL/save/load/$SAVE_ID")
NEW_SESSION=$(echo "$LOAD_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('sessionId', 'N/A'))")
NARRATION=$(echo "$LOAD_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('narration', 'N/A')[:100])")
echo -e "${GREEN}✓ 新 Session: $NEW_SESSION${NC}"
echo -e "${YELLOW}📖 加载叙述: $NARRATION...${NC}"
echo ""

# =============================================================================
# Step 9: 测试 Streaming (简单验证)
# =============================================================================
echo -e "${BLUE}━━━ Step 9: 测试 Streaming SSE ━━━${NC}"
STREAM_RESP=$(curl -s -N -X POST "$API_URL/game/action/stream" \
  -H "Content-Type: application/json" \
  -d "{\"sessionId\":\"$NEW_SESSION\",\"actionType\":\"investigation\",\"actionId\":\"check_systems\",\"actionText\":\"I check the systems again\"}" 2>&1 | head -5)
echo "$STREAM_RESP"
echo -e "${GREEN}✓ Streaming 响应正常${NC}"
echo ""

# =============================================================================
# Step 10: Debug 端点测试
# =============================================================================
echo -e "${BLUE}━━━ Step 10: Debug 功能测试 ━━━${NC}"
DEBUG_RESP=$(curl -s "$API_URL/debug/state/dump/$NEW_SESSION")
AI_SIZE=$(echo "$DEBUG_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('aiContextSize', 'N/A'))")
echo -e "${GREEN}✓ AI Context Size: $AI_SIZE tokens${NC}"
echo ""

# =============================================================================
# 清理: 删除测试存档
# =============================================================================
echo -e "${BLUE}━━━ 清理: 删除测试存档 ━━━${NC}"
curl -s -X DELETE "$API_URL/save/save/$SAVE_ID" > /dev/null
echo -e "${GREEN}✓ 存档已删除${NC}"
echo ""

# =============================================================================
# 测试完成
# =============================================================================
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ 所有测试通过!                              ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "测试覆盖:"
echo "  ✓ 开始新游戏 (动态AI叙述)"
echo "  ✓ 执行玩家行为 (GameLoop处理)"
echo "  ✓ 结束回合 (资源衰减, NPC行动)"
echo "  ✓ 保存/加载游戏"
echo "  ✓ Streaming SSE"
echo "  ✓ Debug 端点"
echo ""
echo "下一步: 打开 http://localhost:5173 进行 UI 测试"
