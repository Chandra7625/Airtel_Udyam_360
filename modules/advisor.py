import os

def explain_recommendation(profile, products):
    fallback = "Based on your business size, location, registration status and budget, these products are eligible in the supplied catalogue. The bundle prioritises reliable business connectivity and relevant add-ons. You can change the selection before checkout."
    key=os.getenv("GEMINI_API_KEY","")
    if not key or products.empty: return fallback
    try:
        from google import genai
        client=genai.Client(api_key=key)
        items=products[["product_id","product_name","description","price_min_inr_per_month","price_max_inr_per_month"]].to_dict('records')
        prompt=("You are Udyam360, a concise multilingual MSME telecom advisor. Explain only these eligible catalogue products; do not invent prices or products. "
                f"Customer profile: {profile}. Eligible recommendations: {items}. Give 3 short reasons and one caution if relevant. Plain language.")
        response=client.models.generate_content(model=os.getenv("GEMINI_MODEL","gemini-2.5-flash"),contents=prompt)
        return response.text or fallback
    except Exception:
        return fallback
