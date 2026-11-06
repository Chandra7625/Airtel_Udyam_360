import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from modules.data_loader import load_catalogue
from modules.recommendations import recommend, eligible_products, validate_bundle
from modules.advisor import explain_recommendation
from modules.pricing import quote
from modules.kyc import lookup_gstin, lookup_udyam, basic_gstin_format_check
from modules.database import create_order, get_orders
from modules.analytics import load_leads, STAGES
from modules.data_loader import load_registry
from modules.kyc import create_kyc_application

st.set_page_config(page_title="Udyam360 | MSME onboarding",page_icon="🏪",layout="wide")

st.markdown("""<style>
.block-container{padding-top:1.4rem;padding-bottom:2rem} .hero{padding:1.5rem;border-radius:18px;background:linear-gradient(120deg,#063b2b,#13845a);color:white} .hero h1{font-size:2.5rem;margin:0} .hero p{opacity:.9;margin-bottom:0} div[data-testid="stMetric"]{background:#f5faf7;padding:14px;border-radius:12px;border:1px solid #e4eee8;color:#173b2d !important}
div[data-testid="stMetric"] [data-testid="stMetricLabel"],
div[data-testid="stMetric"] [data-testid="stMetricLabel"] *,
div[data-testid="stMetric"] [data-testid="stMetricValue"],
div[data-testid="stMetric"] [data-testid="stMetricValue"] *,
div[data-testid="stMetric"] [data-testid="stMetricDelta"],
div[data-testid="stMetric"] [data-testid="stMetricDelta"] *,
div[data-testid="stMetric"] p,
div[data-testid="stMetric"] span{color:#173b2d !important; -webkit-text-fill-color:#173b2d !important}
</style>""",unsafe_allow_html=True)

@st.cache_data
def catalogue(): return load_catalogue()
cat=catalogue()
if "profile" not in st.session_state: st.session_state.profile=None
if "bundle" not in st.session_state: st.session_state.bundle=pd.DataFrame()
if "order_id" not in st.session_state: st.session_state.order_id=None

st.sidebar.markdown("# 🟢 Udyam360")
st.sidebar.caption("Digital onboarding for India's MSMEs")
page=st.sidebar.radio("Navigate",["Home","AI Business Advisor","Bundle & Checkout","Smart KYC","Order Tracker","Sales Intelligence"])

if page=="Home":
    st.markdown('<div class="hero"><h1>Udyam360</h1><p>Make your business digital in one sitting. Discover, bundle, verify and activate — all in one place.</p></div>',unsafe_allow_html=True)
    st.write("")
    a,b,c=st.columns(3); a.metric("Products in catalogue",len(cat)); b.metric("Mock GSTIN records",3534); c.metric("Mock Udyam records",2723)
    st.subheader("Your digital business journey")
    cols=st.columns(4)
    for col,num,title,desc in zip(cols,["01","02","03","04"],["Discover","Choose","Verify","Activate"],["Tell us about your business","Get a transparent bundle quote","Verify registrations with consent","Track installation and activation"]):
        with col:
            st.markdown(f"### {num} · {title}"); st.write(desc)

elif page=="AI Business Advisor":
    st.title("Your business, understood")
    st.write("Answer a few questions. We'll shortlist products using the supplied catalogue's eligibility rules.")
    with st.form("profile_form"):
        c1,c2=st.columns(2)
        with c1:
            business=st.text_input("Business name",placeholder="e.g. Saffron Bakers")
            btype=st.selectbox("Business type",["Kirana store","Salon","Pharmacy","Clinic","Dental clinic","CA firm","Coaching centre","Restaurant","Retail chain","Auto-parts unit","Small manufacturer","Other"])
            segment=st.selectbox("Business segment",["Micro retail & services","Professional offices","Small multi-site businesses","Small manufacturers"])
            employees=st.number_input("Number of employees",1,5000,4)
            sites=st.number_input("Number of locations",1,500,1)
        with c2:
            city=st.text_input("City",value="Chennai")
            tier=st.selectbox("City tier",["1","2"])
            language=st.selectbox("Preferred language",["English","Hindi","Tamil","Bengali","Telugu","Malayalam","Marathi","Kannada","Punjabi"])
            hasgst=st.checkbox("I have a GSTIN")
            budget=st.number_input("Monthly budget (₹)",500,500000,3000,step=250)
            need=st.multiselect("What do you need?",["Reliable internet","Business mobile connectivity","Customer messaging","Cloud email/storage","Cybersecurity","CCTV/POS connectivity"],default=["Reliable internet"])
        submitted=st.form_submit_button("Find my business bundle",type="primary",use_container_width=True)
    if submitted:
        segcode={"Micro retail & services":"micro","Professional offices":"prof","Small multi-site businesses":"multi","Small manufacturers":"mfg"}[segment]
        profile={"business":business or "My Business","business_type":btype,"segment":segment,"segment_code":segcode,"employees":int(employees),"sites":int(sites),"city":city,"city_tier":tier,"language":language,"has_gstin":hasgst,"budget":budget,"needs":need}
        st.session_state.profile=profile
        bundle,why=recommend(cat,profile,budget)
        st.session_state.bundle=bundle
        st.session_state.recommendation_why=why
    if st.session_state.profile:
        p=st.session_state.profile; bundle=st.session_state.bundle
        st.success(f"Profile saved for {p['business']} · {p['language']}")
        st.subheader("Recommended bundle")
        st.write(explain_recommendation(p,bundle))
        if not bundle.empty:
            display=bundle[["product_id","product_name","description","price_min_inr_per_month","price_max_inr_per_month","typical_install_days"]].copy()
            display.columns=["ID","Product","What it does","Monthly from (₹)","Monthly up to (₹)","Install days"]
            st.dataframe(display,use_container_width=True,hide_index=True)
            _,monthly,setup,contract=quote(bundle)
            x,y,z=st.columns(3); x.metric("Estimated monthly",f"₹{monthly:,.0f}"); y.metric("One-time setup",f"₹{setup:,.0f}"); z.metric("Minimum contract",f"{contract} months")
            st.info("Prices shown as catalogue midpoint estimates. Confirm final selected products and price in Bundle & Checkout.")
            st.caption("Next: open **Bundle & Checkout** from the left navigation to confirm your selected products.")

elif page=="Bundle & Checkout":
    st.title("Build your bundle")
    if st.session_state.profile is None:
        st.warning("Complete your business profile in AI Business Advisor first.")
    else:
        p=st.session_state.profile; st.caption(f"Quote for {p['business']} · {p['city']}")
        eligible=eligible_products(cat,p)
        if eligible.empty: st.warning("No products are eligible for this profile.")
        else:
            default=list(st.session_state.bundle.product_id.astype(str)) if not st.session_state.bundle.empty else []
            selected=st.multiselect("Choose products",options=eligible.product_id.astype(str).tolist(),default=[x for x in default if x in eligible.product_id.astype(str).tolist()],format_func=lambda x: f"{x} · {eligible.loc[eligible.product_id.astype(str)==x,'product_name'].iloc[0]}")
            bundle=eligible[eligible.product_id.astype(str).isin(selected)].copy()
            errors=validate_bundle(bundle,p)
            if errors:
                for e in errors: st.error(e)
            q,monthly,setup,contract=quote(bundle)
            if not q.empty:
                st.dataframe(q[["product_id","product_name","monthly_price_inr","setup_fee_inr"]].rename(columns={"product_id":"ID","product_name":"Product","monthly_price_inr":"Monthly estimate ₹","setup_fee_inr":"Setup ₹"}),use_container_width=True,hide_index=True)
            a,b,c=st.columns(3); a.metric("Monthly total",f"₹{monthly:,.0f}"); b.metric("Setup total",f"₹{setup:,.0f}"); c.metric("Contract",f"{contract} months")
            if st.button("Confirm quote & place demo order",type="primary",disabled=not selected or bool(errors)):
                st.session_state.bundle=bundle
                oid=create_order(p['business'],", ".join(bundle.product_name.astype(str)),monthly,setup)
                st.session_state.order_id=oid
                st.success(f"Demo order created: {oid}. Go to Order Tracker.")


elif page == "Smart KYC":
    st.title("Smart KYC verification")
    st.warning(
        "This prototype uses fictional mock registries. "
        "It is not connected to GSTN, Udyam or DigiLocker."
    )

    consent = st.checkbox(
        "I consent to use the details entered below for this simulated "
        "KYC verification. I understand this demo stores no uploaded "
        "document permanently."
    )

    st.subheader("Business and outlet details")

    business_name = st.text_input(
        "Business / trade name",
        placeholder="e.g. Saffron Bakers"
    )

    outlet_name = st.text_input(
        "Outlet name or location",
        placeholder="e.g. Saffron Bakers - Visakhapatnam"
    )

    if business_name.strip():
        gst_df = load_registry("mock_gstin_registry.csv", "gstin")
        ud_df = load_registry("mock_udyam_registry.csv", "udyam_number")

        # Find all GST registrations using the trade name
        gst_matches = gst_df[
            gst_df["trade_name"].astype(str).str.strip().str.casefold()
            == business_name.strip().casefold()
        ]

        # Find all Udyam registrations using the enterprise name
        ud_matches = ud_df[
            ud_df["enterprise_name"].astype(str).str.strip().str.casefold()
            == business_name.strip().casefold()
        ]

        st.divider()
        st.subheader("Select registrations for this outlet")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**GST registrations**")

            if not gst_matches.empty:
                gst_options = [""] + gst_matches["gstin"].astype(str).tolist()

                selected_gst = st.selectbox(
                    "Select the applicable GSTIN",
                    gst_options,
                    format_func=lambda x: x if x else "Select GSTIN",
                    key="selected_outlet_gstin"
                )
            else:
                selected_gst = ""
                st.info("No matching GSTIN registrations found.")

        with col2:
            st.markdown("**Udyam registrations**")

            if not ud_matches.empty:
                ud_options = [""] + ud_matches["udyam_number"].astype(str).tolist()

                selected_ud = st.selectbox(
                    "Select the applicable Udyam number",
                    ud_options,
                    format_func=lambda x: x if x else "Select Udyam number",
                    key="selected_outlet_udyam"
                )
            else:
                selected_ud = ""
                st.info("No matching Udyam registrations found.")

        st.divider()
        st.subheader("Verify selected registrations")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Verify selected GSTIN",
                disabled=not consent or not selected_gst
            ):
                if not basic_gstin_format_check(selected_gst):
                    st.error("GSTIN format check failed.")
                else:
                    res = lookup_gstin(selected_gst)
                    st.write("**Status:**", res["status"])
                    st.info(res["message"])

                    if res.get("record"):
                        st.json(res["record"])

        with col2:
            if st.button(
                "Verify selected Udyam",
                disabled=not consent or not selected_ud
            ):
                res = lookup_udyam(selected_ud)
                st.write("**Status:**", res["status"])
                st.info(res["message"])

                if res.get("record"):
                    st.json(res["record"])

        if selected_gst and selected_ud:
            st.warning(
                "Cross-registry relationship has not been independently "
                "established. Manual Review Required. Selecting both "
                "registrations does not prove that they belong together."
            )

    else:
        st.info("Enter a business name to find its available registrations.")

    st.divider()
    st.subheader("Supporting document upload")

    st.caption(
        "Documents can be uploaded even if the business is absent "
        "from either mock registry."
    )

    uploaded = st.file_uploader(
        "Upload specimen document (PDF, JPG or PNG)",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    if uploaded:
        for file in uploaded:
            st.success(
                f"Received {file.name} ({file.size:,} bytes). "
                "Pending manual review."
            )

        st.info(
            "OCR and automatic document verification are not enabled "
            "in this MVP. Uploading a document does not mean it is verified."
        )

elif page=="Order Tracker":
    st.title("Track your order")
    orders=get_orders()
    if st.session_state.order_id: st.success(f"Your latest order reference: **{st.session_state.order_id}**")
    if not orders: st.info("No demo orders yet. Create one through Bundle & Checkout.")
    else:
        for o in orders:
            with st.expander(f"{o[0]} · {o[1]} · ₹{o[3]:,.0f}/month",expanded=(o[0]==st.session_state.order_id)):
                st.write("Products:",o[2]); st.write("Created:",o[6]); st.write("Status:",o[5])
                steps=["Order confirmed","KYC review","Installation scheduled","Activated"]
                st.progress(0.25); st.caption("Order confirmed → KYC review → Installation scheduled → Activated")
                st.caption("Demo status is simulated. Real activation requires operational integration.")

elif page=="Sales Intelligence":
    st.title("Sales intelligence")
    st.caption("Uses the original supplied lead-level dataset when available; otherwise uses clearly labelled synthetic demo data.")
    df, data_source=load_leads()
    st.caption(f"Data source: {data_source}")
    activated=df[df.outcome=="Activated"]
    m1,m2,m3,m4=st.columns(4); m1.metric("Leads",f"{len(df):,}"); m2.metric("Activated",f"{len(activated):,}"); m3.metric("Activation rate",f"{len(activated)/len(df)*100:.1f}%"); m4.metric("Avg. follow-up calls",f"{df.customer_follow_up_calls.mean():.1f}")
    if "stage_reached" in df.columns and "smb_leads.csv" in data_source:
        stage_order = ["Lead", "Contacted", "Needs assessed", "Quote accepted", "KYC complete", "Activated"]
        counts = df["stage_reached"].value_counts()
        funnel = pd.DataFrame({"Stage": stage_order, "Leads": [int(counts.get(s, 0)) for s in stage_order]})
    else:
        funnel=pd.DataFrame(STAGES,columns=["Stage","Leads"])
    st.subheader("Acquisition funnel"); st.plotly_chart(px.funnel(funnel,x="Leads",y="Stage",title="Published case-study funnel baseline"),use_container_width=True)
    l,r=st.columns(2)
    with l: st.subheader("Leads by segment"); st.plotly_chart(px.histogram(df,x="segment",color="outcome",barmode="group"),use_container_width=True)
    with r: st.subheader("Lead source mix"); st.plotly_chart(px.histogram(df,x="lead_source",color="outcome",barmode="group"),use_container_width=True)
    st.subheader("Drop reasons" if "smb_leads.csv" in data_source else "Drop reasons (synthetic sample)"); drops=df[df.outcome=="Dropped"].drop_reason.value_counts().head(8).rename_axis("Reason").reset_index(name="Leads"); st.plotly_chart(px.bar(drops,x="Leads",y="Reason",orientation="h"),use_container_width=True)
    st.download_button("Download leads data",df.to_csv(index=False).encode(),"udyam360_leads_export.csv","text/csv")

