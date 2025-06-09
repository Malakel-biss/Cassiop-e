def get_transcript_from_time(start_time, end_time=None, transcript_json=None):
    from datetime import timedelta

    def time_to_seconds(time_str):
        mins, secs = map(int, time_str.split(":"))
        return mins * 60 + secs

    if not transcript_json:
        return ""

    start = time_to_seconds(start_time)
    end = time_to_seconds(end_time) if end_time else start + 15

    # Filter lines between start and end
    filtered = [
        segment["text"] for segment in transcript_json
        if float(segment["start"]) >= start and float(segment["end"]) <= end
    ]
    return "\n".join(filtered)
