from tiangong.animations import play_full_boot_sequence, play_grade_promotion_alert, play_tribulation_alert

if __name__ == "__main__":
    print("=== TESTING BOOT SEQUENCE ===")
    play_full_boot_sequence()

    print("=== TESTING TRIBULATION ALERT ===")
    play_tribulation_alert("结丹期", "元婴期")

    print("=== TESTING GRADE PROMOTION ===")
    play_grade_promotion_alert("LangChain", "天阶上等")

    print("ALL DONE")
