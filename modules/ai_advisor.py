# import google.generativeai as genai
# import os
# import time

# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# def get_ai_recommendation(patient_name, disease_name, param_trends, param_values):
#     """
#     patient_name  : str
#     disease_name  : str  — e.g. "Type 2 Diabetes"
#     param_trends  : dict — {"HbA1c": "worsening", "Fasting Sugar": "stable"}
#     param_values  : dict — {"HbA1c": [8.2, 8.5, 8.8], "Fasting Sugar": [180, 190, 200]}
#     """

#     # Build dynamic parameter summary
#     param_summary = ""
#     for param, values in param_values.items():
#         trend = param_trends.get(param, "stable")
#         if values:
#             latest = values[-1]
#             param_summary += f"\n- {param}: latest = {latest}, trend = {trend}, history = {values}"

#     prompt = f"""
# You are an experienced clinical decision support assistant helping doctors in India.

# Patient: {patient_name}
# Disease: {disease_name}

# Latest Lab Parameters:
# {param_summary}

# Based on the above data, provide:
# 1. A brief clinical assessment (2-3 lines)
# 2. Key concerns if any parameters are worsening or spiking
# 3. Specific actionable recommendations for the doctor (medication review, lifestyle, follow-up)
# 4. Suggested follow-up timeline

# Keep the response concise, professional, and medically accurate.
# Remember: This is decision support only — final call is with the treating physician.
# """

#     model = genai.GenerativeModel("gemini-2.5-flash")

#     for attempt in range(3):
#         try:
#             response = model.generate_content(prompt)
#             return response.text
#         except Exception as e:
#             if "429" in str(e) or "quota" in str(e).lower():
#                 time.sleep(2 ** attempt)
#                 continue
#             raise e

#     return "⚠️ AI recommendation temporarily unavailable. Please try again later."


from google import genai
import os
import time

def get_ai_recommendation(patient_name, disease_name, param_trends, param_values):

    # Initialize client inside function so .env is already loaded
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Build dynamic parameter summary
    param_summary = ""
    for param, values in param_values.items():
        trend  = param_trends.get(param, "stable")
        latest = values[-1] if values else "N/A"
        param_summary += f"\n- {param}: latest = {latest}, trend = {trend}, history = {values}"

    prompt = f"""
You are an experienced clinical decision support assistant helping doctors in India.

Patient: {patient_name}
Disease: {disease_name}

Latest Lab Parameters:
{param_summary}

Based on the above data, provide:
1. A brief clinical assessment (2-3 lines)
2. Key concerns if any parameters are worsening or spiking
3. Specific actionable recommendations for the doctor (medication review, lifestyle, follow-up)
4. Suggested follow-up timeline

Keep the response concise, professional, and medically accurate.
Remember: This is decision support only — final call is with the treating physician.
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                time.sleep(2 ** attempt)
                continue
            raise e

    return "AI recommendation temporarily unavailable. Please try again later."