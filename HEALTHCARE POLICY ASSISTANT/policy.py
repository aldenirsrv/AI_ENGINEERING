from __future__ import annotations

import textwrap
from typing import List, TypedDict


class PolicyMetadata(TypedDict, total=False):
    policy_id: str
    category: str
    status: str
    plan: str
    region: str
    effective_date: str
    department: str


class PolicyDoc(TypedDict):
    text: str
    metadata: PolicyMetadata


def _t(text: str) -> str:
    return textwrap.dedent(text).strip()


policy_docs: List[PolicyDoc] = [
    {
        "text": _t(
            """
            SECTION 1: ELIGIBILITY

            Patients enrolled in Plan A are eligible for outpatient rehabilitation services.
            Coverage begins after policy activation and completion of the deductible.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Eligibility",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 2: PRIMARY CARE VISITS

            General practitioner visits are fully covered when provided by approved providers.
            Walk-in clinics are included under outpatient services.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Primary Care",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 3: SPECIALIST REFERRALS

            Specialist consultations require a physician referral unless the consultation is categorized as urgent care.
            Without a referral, reimbursement is reduced to 50%.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Referrals",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 4: PHYSIOTHERAPY COVERAGE

            Physiotherapy sessions are covered when medically necessary.
            Coverage includes up to 20 sessions annually.
            Additional sessions require prior authorization.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Physiotherapy",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 5: POST-SURGICAL REHABILITATION

            Rehabilitation following knee surgery includes up to 30 physiotherapy sessions when prescribed by a surgeon.
            Coverage applies only to in-network rehabilitation clinics.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Rehabilitation",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 6: MENTAL HEALTH SERVICES

            Psychological counseling is covered for up to 10 sessions annually with a licensed provider.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Mental Health",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 7: DIAGNOSTIC IMAGING

            MRI and CT imaging require prior authorization except in emergency situations.
            Standard X-rays do not require approval.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Diagnostics",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 8: PRESCRIPTION DRUGS

            Prescription medications approved under the provincial formulary are covered at 80%.
            Experimental medications are excluded unless approved through exception review.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Pharmacy",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 9: EMERGENCY SERVICES

            Emergency room visits are fully covered across British Columbia hospitals.
            Out-of-province emergency care is reimbursed according to provincial limits.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Emergency",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 10: OUT-OF-NETWORK COVERAGE

            Out-of-network services are reimbursed at 60% of eligible expenses unless otherwise stated.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Network",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 11: PRIOR AUTHORIZATION

            The following services require prior authorization:
            - Extended physiotherapy
            - MRI imaging
            - Non-emergency surgery
            - Inpatient rehabilitation
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Authorization",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 12: PEDIATRIC SERVICES

            Children under 18 are eligible for developmental physiotherapy assessments and rehabilitation programs.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Pediatrics",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 13: MATERNITY CARE

            Prenatal physiotherapy and postpartum rehabilitation are included under outpatient maternal care.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Maternity",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 14: SENIOR CARE

            Patients over age 65 may qualify for extended rehabilitation benefits following hospitalization.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Senior Care",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 15: HOME HEALTH SERVICES

            Home physiotherapy visits are covered when prescribed by a primary care physician.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Home Care",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 16: EXCLUSIONS

            Experimental procedures and non-medically necessary rehabilitation are not covered.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Exclusions",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 17: CLAIM SUBMISSION

            Claims must be submitted within 90 days of the treatment date.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Claims",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 18: APPEALS PROCESS

            Coverage denials may be appealed within 30 days with supporting medical documentation.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Appeals",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 19: SUPERSEDED POLICY VERSION

            The previous version of this policy covered only 15 physiotherapy sessions annually.
            This document is no longer active.
            """
        ),
        "metadata": {
            "policy_id": "POL-2024-0042",
            "category": "Physiotherapy",
            "status": "Superseded",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 20: TELEHEALTH SERVICES

            Virtual rehabilitation consultations are covered when delivered by approved providers within British Columbia.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Telehealth",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
    {
        "text": _t(
            """
            SECTION 21: PREVENTIVE CARE AND WELLNESS VISITS

            Annual wellness visits are covered at 100% when provided once per calendar year
            by an approved in-network primary care provider.

            Preventive screenings recommended during the annual wellness visit are covered
            when they are part of the approved preventive care schedule.

            Additional wellness visits in the same calendar year may be billed as standard
            primary care visits unless medically necessary.
            """
        ),
        "metadata": {
            "policy_id": "POL-2026-0042",
            "category": "Preventive Care",
            "status": "Active",
            "plan": "Plan A",
            "region": "British Columbia",
            "effective_date": "2026-01-01",
        },
    },
]

