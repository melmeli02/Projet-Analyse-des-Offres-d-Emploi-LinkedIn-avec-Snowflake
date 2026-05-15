import streamlit as st
import altair as alt
from snowflake.snowpark.context import get_active_session

st.title("Dashboard d'analyse des offres Linkedin")

session = get_active_session()

analyse = st.sidebar.selectbox(
    "Choisir une analyse",
    [
        "Analyse 1 : Top titres par industrie",
        "Analyse 2 : Top salaires par industrie",
        "Analyse 3 : Répartition par taille d'entreprise",
        "Analyse 4 : Répartition par secteur",
        "Analyse 5 : Répartition par type d'emploi"
    ]
)

if analyse == "Analyse 1 : Top titres par industrie":

    st.subheader("Analyse 1 : Top 10 des titres les plus publiés par industrie")

    query = """
    SELECT
        ci.industry AS industrie,
        jp.title AS titre,
        COUNT(*) AS nb_offres,
        ROW_NUMBER() OVER (
            PARTITION BY ci.industry
            ORDER BY COUNT(*) DESC
        ) AS classement
    FROM LINKEDIN.RAW.JOB_POSTINGS jp
    JOIN LINKEDIN.RAW.COMPANIES c
        ON SPLIT_PART(jp.company_name, '.', 1) = c.company_id
    JOIN LINKEDIN.RAW.COMPANY_INDUSTRIES ci
        ON c.company_id = ci.company_id
    GROUP BY ci.industry, jp.title
    QUALIFY classement <= 10
    ORDER BY ci.industry, nb_offres DESC
    """

    df = session.sql(query).to_pandas()

    industrie = st.selectbox(
        "Choisir une industrie",
        sorted(df["INDUSTRIE"].dropna().unique())
    )

    df_filtre = df[df["INDUSTRIE"] == industrie]

    st.dataframe(df_filtre, use_container_width=True)

    st.bar_chart(
        data=df_filtre,
        x="TITRE",
        y="NB_OFFRES"
    )

elif analyse == "Analyse 2 : Top salaires par industrie":

    st.subheader("Analyse 2 : Top 10 des postes les mieux rémunérés par industrie")

    query = """
    SELECT
        ci.industry AS industrie,
        jp.title AS titre,
        ROUND(AVG(TRY_CAST(jp.max_salary AS FLOAT)), 0) AS salaire_max_moyen,
        ROW_NUMBER() OVER (
            PARTITION BY ci.industry
            ORDER BY AVG(TRY_CAST(jp.max_salary AS FLOAT)) DESC
        ) AS classement
    FROM LINKEDIN.RAW.JOB_POSTINGS jp
    JOIN LINKEDIN.RAW.COMPANIES c
        ON SPLIT_PART(jp.company_name, '.', 1) = c.company_id
    JOIN LINKEDIN.RAW.COMPANY_INDUSTRIES ci
        ON c.company_id = ci.company_id
    WHERE jp.max_salary IS NOT NULL
    AND jp.max_salary != ''
    GROUP BY ci.industry, jp.title
    QUALIFY classement <= 10
    ORDER BY ci.industry, salaire_max_moyen DESC
    """

    df = session.sql(query).to_pandas()

    industrie = st.selectbox(
        "Choisir une industrie",
        sorted(df["INDUSTRIE"].dropna().unique())
    )

    df_filtre = df[df["INDUSTRIE"] == industrie]

    st.dataframe(df_filtre, use_container_width=True)

    st.bar_chart(
        data=df_filtre,
        x="TITRE",
        y="SALAIRE_MAX_MOYEN"
    )

elif analyse == "Analyse 3 : Répartition par taille d'entreprise":

    st.subheader("Analyse 3 : Répartition des offres par taille d'entreprise")

    query = """
    SELECT
        CASE c.company_size
            WHEN '0' THEN 'Solo'
            WHEN '1' THEN '1-10 employés'
            WHEN '2' THEN '11-50 employés'
            WHEN '3' THEN '51-200 employés'
            WHEN '4' THEN '201-500 employés'
            WHEN '5' THEN '501-1000 employés'
            WHEN '6' THEN '1001-5000 employés'
            WHEN '7' THEN '5000+ employés'
        END AS taille,
        COUNT(jp.job_id) AS nb_offres
    FROM LINKEDIN.RAW.JOB_POSTINGS jp
    JOIN LINKEDIN.RAW.COMPANIES c
        ON SPLIT_PART(jp.company_name, '.', 1) = c.company_id
    GROUP BY c.company_size, taille
    ORDER BY c.company_size
    """

    df = session.sql(query).to_pandas()

    st.table(df)

    chart = alt.Chart(df).mark_arc(innerRadius=50).encode(
        theta="NB_OFFRES:Q",
        color="TAILLE:N",
        tooltip=["TAILLE", "NB_OFFRES"]
    )

    st.altair_chart(chart, use_container_width=True)

elif analyse == "Analyse 4 : Répartition par secteur":

    st.subheader("Analyse 4 : Répartition des offres par secteur d'activité")

    query = """
    SELECT
        ci.industry AS secteur,
        COUNT(DISTINCT jp.job_id) AS nb_offres
    FROM LINKEDIN.RAW.JOB_POSTINGS jp
    JOIN LINKEDIN.RAW.COMPANIES c
        ON SPLIT_PART(jp.company_name, '.', 1) = c.company_id
    JOIN LINKEDIN.RAW.COMPANY_INDUSTRIES ci
        ON c.company_id = ci.company_id
    GROUP BY ci.industry
    ORDER BY nb_offres DESC
    LIMIT 20
    """

    df = session.sql(query).to_pandas()

    st.table(df)

    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X("NB_OFFRES:Q", title="Nombre d'offres"),
        y=alt.Y("SECTEUR:N", sort="-x", title="Secteur"),
        tooltip=["SECTEUR", "NB_OFFRES"]
    )

    st.altair_chart(chart, use_container_width=True)

elif analyse == "Analyse 5 : Répartition par type d'emploi":

    st.subheader("Analyse 5 : Répartition par type d'emploi")

    query = """
    SELECT
        formatted_work_type AS type_emploi,
        COUNT(*) AS nb_offres,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pourcentage
    FROM LINKEDIN.RAW.JOB_POSTINGS
    WHERE formatted_work_type IS NOT NULL
    AND formatted_work_type != ''
    GROUP BY formatted_work_type
    ORDER BY nb_offres DESC
    """

    df = session.sql(query).to_pandas()

    st.table(df)

    chart = alt.Chart(df).mark_arc(innerRadius=60).encode(
        theta="NB_OFFRES:Q",
        color="TYPE_EMPLOI:N",
        tooltip=["TYPE_EMPLOI", "NB_OFFRES", "POURCENTAGE"]
    )

    st.altair_chart(chart, use_container_width=True)