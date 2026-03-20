class PromptBuilder:
    @staticmethod
    def build_system_prompt(base_script: str, slot_data: dict[str, str], language: str = "en") -> str:
        lang_names = {"en": "English", "ru": "Russian", "ro": "Romanian"}
        lang_name = lang_names.get(language, "English")
        caller_name = slot_data.get("patient_name") or slot_data.get("customer_name") or slot_data.get("contact_name") or slot_data.get("guest_name") or slot_data.get("booked_name") or slot_data.get("policyholder_name")

        identity = f"Your name is {caller_name}. " if caller_name else "You are a personal assistant. "

        prompt = (
            f"{identity}"
            "You are already on an active phone call — someone picked up and is listening. "
            "Start speaking immediately with a natural greeting.\n\n"
            f"LANGUAGE: You MUST speak ONLY in {lang_name}. All your responses must be in {lang_name}.\n\n"
            f"YOUR OBJECTIVE (internal instructions — do NOT read these aloud): {base_script}\n\n"
        )
        if slot_data:
            prompt += "Details to use in the conversation (use EXACT values, do NOT modify names):\n"
            for key, value in slot_data.items():
                prompt += f"- {key.replace('_', ' ').title()}: {value}\n"

        prompt += (
            "\nCRITICAL RULES:\n"
            "- Introduce yourself naturally by your name (e.g., 'Bună ziua, sunt Eva' / 'Hello, this is Eva')\n"
            "- NEVER say 'on behalf of' or 'din partea' — you ARE the person, not an assistant\n"
            "- NEVER use placeholders like [Name], [Numele tău] — use the actual values above\n"
            "- Be polite and natural. Confirm details before ending.\n"
            "- When the objective is achieved, end politely and include [OBJECTIVE_ACHIEVED] in your final message.\n"
            "- If the objective clearly cannot be achieved (refusal, unavailability), include [OBJECTIVE_FAILED].\n"
            "- Keep responses concise (1-2 sentences) since this is a phone conversation."
        )
        return prompt

    @staticmethod
    def build_summary_prompt(language: str = "en") -> str:
        lang_names = {"en": "English", "ru": "Russian", "ro": "Romanian"}
        lang_name = lang_names.get(language, "English")
        return (
            f"Summarize this phone conversation in 2-3 sentences in {lang_name}. "
            "Include the outcome (success/failure) and any confirmed details. "
            f"Write the summary ONLY in {lang_name}."
        )
