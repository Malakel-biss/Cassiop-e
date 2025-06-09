memory_by_video = {}

def add_to_memory(video_id, user_msg, bot_response):
    if video_id not in memory_by_video:
        memory_by_video[video_id] = []
    memory_by_video[video_id].append({"user": user_msg, "bot": bot_response})

def get_memory(video_id):
    return memory_by_video.get(video_id, [])

def reset_memory(video_id):
    memory_by_video[video_id] = []
