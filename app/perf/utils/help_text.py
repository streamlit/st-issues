def get_help_text(metric_name: str) -> str:
    doc_parts = []

    if "long_animation_frame" in metric_name:
        doc_parts.append(
            "A long animation frame is a frame that takes longer than 16.67ms to render, causing potential jank or stutter in animations."
        )

    if "_mount_" in metric_name:
        doc_parts.append(
            "Mount indicates when the component is first added to the DOM and rendered for the first time."
        )

    if "_nested-update_" in metric_name:
        doc_parts.append(
            "Nested updates are scheduled in a layout effect and processed synchronously by React, delaying paint and blocking the main thread. These should be avoided when possible."
        )

    if "_update_" in metric_name:
        doc_parts.append(
            "Update indicates when a component is re-rendered due to changes in state or props, potentially causing performance issues if too frequent or unnecessary."
        )

    if "_count" in metric_name:
        doc_parts.append("Count indicates the total number of times this event occurred during the test.")

    if "_duration_ms" in metric_name:
        doc_parts.append(
            "Total duration (ms) indicates the total summed duration in milliseconds these events took during the test."
        )

    doc_parts.append(
        "See [Interpreting Playwright Performance Metrics](playwright_interpreting_results) for more information."
    )

    return "\n\n".join(doc_parts)
