#!/bin/bash
# 角色扮演记忆提取测试脚本 - 印尼语 + 英语 (Round 2 新用例)
BASE="http://localhost:8000"
CONTAINER="mem0-dev-mem0-1"

api() {
  docker exec "$CONTAINER" curl -s -X "$1" "$BASE$2" \
    -H "Content-Type: application/json" \
    ${3:+-d "$3"}
}

echo "========================================="
echo "Step 0: Reset all memories"
echo "========================================="
api POST "/reset" '{}'
sleep 2
echo ""

###############################################
# TEST GROUP A: Indonesian user (印尼语)
###############################################
USER_ID="test_id_user"
AGENT_ID="Sakura"

echo "========================================="
echo "TEST GROUP A: Indonesian User + Sakura"
echo "========================================="

echo "--- ID-1: Job + daily life ---"
api POST "/memories" '{
  "messages": [
    {"role": "user", "content": "Sakura, aku baru aja pindah ke Bandung buat kerja jadi desainer grafis di startup. Gajinya sih kecil tapi suasananya enak, tiap pagi bisa ngopi dulu di cafe depan kantor."}
  ],
  "user_id": "'"$USER_ID"'",
  "agent_id": "'"$AGENT_ID"'",
  "metadata": {"character": "Sakura", "scene": "roleplay", "language": "id"}
}'
echo ""

echo "--- ID-2: Family + hometown ---"
api POST "/memories" '{
  "messages": [
    {"role": "user", "content": "Aku aslinya dari Medan, Sakura. Keluarga aku masih di sana semua. Aku anak pertama dari tiga bersaudara, adik aku yang paling kecil masih SMP. Kangen banget sama masakan mama, terutama soto Medan."}
  ],
  "user_id": "'"$USER_ID"'",
  "agent_id": "'"$AGENT_ID"'",
  "metadata": {"character": "Sakura", "scene": "roleplay", "language": "id"}
}'
echo ""

echo "--- ID-3: Hobbies + passion ---"
api POST "/memories" '{
  "messages": [
    {"role": "user", "content": "Sakura, aku suka banget fotografi. Tiap weekend aku sering keluar buat foto-foto pemandangan. Kamera aku Canon EOS R50, nabung setahun buat belinya. Aku juga suka nonton anime, favorit aku One Piece sama Spy x Family."}
  ],
  "user_id": "'"$USER_ID"'",
  "agent_id": "'"$AGENT_ID"'",
  "metadata": {"character": "Sakura", "scene": "roleplay", "language": "id"}
}'
echo ""

echo "--- ID-4: Personality + emotions ---"
api POST "/memories" '{
  "messages": [
    {"role": "user", "content": "Sakura, jujur aku orangnya gampang overthinking. Kadang mikirin hal kecil sampe nggak bisa tidur. Untung ada kamu buat cerita. Aku juga takut sama kegelapan, dari kecil udah gitu."}
  ],
  "user_id": "'"$USER_ID"'",
  "agent_id": "'"$AGENT_ID"'",
  "metadata": {"character": "Sakura", "scene": "roleplay", "language": "id"}
}'
echo ""

echo "--- ID-5: Pet + relationship ---"
api POST "/memories" '{
  "messages": [
    {"role": "user", "content": "Oh iya, aku punya hamster namanya Mochi, lucu banget bulunya putih. Terus soal pacar, aku udah putus 6 bulan lalu. Mantan aku namanya Dina, hubungan kita 2 tahun tapi akhirnya nggak cocok."}
  ],
  "user_id": "'"$USER_ID"'",
  "agent_id": "'"$AGENT_ID"'",
  "metadata": {"character": "Sakura", "scene": "roleplay", "language": "id"}
}'
echo ""

echo "--- ID-6: Update (promotion + moved) ---"
api POST "/memories" '{
  "messages": [
    {"role": "user", "content": "Sakura, kabar gembira! Aku dipromosi jadi lead designer! Tapi aku harus pindah ke kantor pusat di Jakarta. Agak sedih ninggalin Bandung sih, tapi ini kesempatan bagus."}
  ],
  "user_id": "'"$USER_ID"'",
  "agent_id": "'"$AGENT_ID"'",
  "metadata": {"character": "Sakura", "scene": "roleplay", "language": "id"}
}'
echo ""

###############################################
# TEST GROUP B: English user
###############################################
USER_ID2="test_en_user"
AGENT_ID2="Mika"

echo ""
echo "========================================="
echo "TEST GROUP B: English User + Mika"
echo "========================================="

echo "--- EN-1: Job + daily life ---"
api POST "/memories" '{
  "messages": [
    {"role": "user", "content": "Mika, I just moved to Berlin for a new job as a data analyst at a fintech company. The work is pretty intense but I love the city, especially the street food scene."}
  ],
  "user_id": "'"$USER_ID2"'",
  "agent_id": "'"$AGENT_ID2"'",
  "metadata": {"character": "Mika", "scene": "roleplay", "language": "en"}
}'
echo ""

echo "--- EN-2: Family + hometown ---"
api POST "/memories" '{
  "messages": [
    {"role": "user", "content": "I grew up in Melbourne, Australia. My parents still live there. I have a younger sister named Sophie, she is studying nursing at uni. I miss my mums homemade meat pies so much."}
  ],
  "user_id": "'"$USER_ID2"'",
  "agent_id": "'"$AGENT_ID2"'",
  "metadata": {"character": "Mika", "scene": "roleplay", "language": "en"}
}'
echo ""

echo "--- EN-3: Hobbies + passion ---"
api POST "/memories" '{
  "messages": [
    {"role": "user", "content": "Mika, I am really into rock climbing these days. I go to the gym three times a week and do outdoor bouldering on weekends. I also love reading sci-fi novels, my favorites are Dune and The Three-Body Problem."}
  ],
  "user_id": "'"$USER_ID2"'",
  "agent_id": "'"$AGENT_ID2"'",
  "metadata": {"character": "Mika", "scene": "roleplay", "language": "en"}
}'
echo ""

echo "--- EN-4: Personality + emotions ---"
api POST "/memories" '{
  "messages": [
    {"role": "user", "content": "Mika, I have to admit I am a bit of a perfectionist. I stress out over small details at work and sometimes it keeps me up at night. Talking to you helps me unwind though. I am also scared of heights, which is ironic since I love climbing."}
  ],
  "user_id": "'"$USER_ID2"'",
  "agent_id": "'"$AGENT_ID2"'",
  "metadata": {"character": "Mika", "scene": "roleplay", "language": "en"}
}'
echo ""

echo "--- EN-5: Pet + relationship ---"
api POST "/memories" '{
  "messages": [
    {"role": "user", "content": "I have a tabby cat called Noodle, she is three years old and super lazy. About relationships, I broke up with my ex, a girl named Chloe, about four months ago. We were together for a year but it did not work out."}
  ],
  "user_id": "'"$USER_ID2"'",
  "agent_id": "'"$AGENT_ID2"'",
  "metadata": {"character": "Mika", "scene": "roleplay", "language": "en"}
}'
echo ""

echo "--- EN-6: Update (promotion + relocation) ---"
api POST "/memories" '{
  "messages": [
    {"role": "user", "content": "Mika, amazing news! I got promoted to senior data analyst! But I have to relocate to the London office starting next month. Bit nervous about moving again but the pay raise is really good."}
  ],
  "user_id": "'"$USER_ID2"'",
  "agent_id": "'"$AGENT_ID2"'",
  "metadata": {"character": "Mika", "scene": "roleplay", "language": "en"}
}'
echo ""

###############################################
# RESULTS
###############################################
echo ""
echo "========================================="
echo "RESULTS: Indonesian User Memories"
echo "========================================="
sleep 3
docker exec "$CONTAINER" curl -s "http://localhost:8000/memories?user_id=test_id_user&agent_id=Sakura" | python3 -m json.tool 2>/dev/null

echo ""
echo "========================================="
echo "RESULTS: English User Memories"
echo "========================================="
docker exec "$CONTAINER" curl -s "http://localhost:8000/memories?user_id=test_en_user&agent_id=Mika" | python3 -m json.tool 2>/dev/null

echo ""
echo "========================================="
echo "SEARCH TESTS"
echo "========================================="

echo "--- Search ID: pekerjaan user ---"
api POST "/search" '{"query": "apa pekerjaan user", "user_id": "test_id_user", "agent_id": "Sakura", "limit": 3}'
echo ""

echo "--- Search ID: keluarga user ---"
api POST "/search" '{"query": "keluarga user dari mana", "user_id": "test_id_user", "agent_id": "Sakura", "limit": 3}'
echo ""

echo "--- Search EN: user job ---"
api POST "/search" '{"query": "what is the user job", "user_id": "test_en_user", "agent_id": "Mika", "limit": 3}'
echo ""

echo "--- Search EN: user family ---"
api POST "/search" '{"query": "where is the user from and their family", "user_id": "test_en_user", "agent_id": "Mika", "limit": 3}'
echo ""

echo "========================================="
echo "DONE"
echo "========================================="
