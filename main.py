from utility.llama import chatter

chatter = chatter("~/dev/llm/Harbinger-24B-Q5_K_M.gguf")

while True:
    player_message = input("Player:")
    if player_message.lower() in ["exit", "quit", "bye"]:
        break
    print(chatter.chat(player_message))
