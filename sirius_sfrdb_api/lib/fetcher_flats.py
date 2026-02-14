#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger('fetcher_flats')


def yn(v):
    return "Y" if v is True else ("N" if v is False else None)


def flat_account(rec, batch_id, extracted_at):
    c = rec.get("country") or {}
    hq = rec.get("hqAddress") or {}
    hc = hq.get("country") or {}
    meta = rec.get("accountMetadata") or {}
    at = meta.get("accountType") or {}
    return {
        "account_id": rec.get("id"),
        "country_id": c.get("id"), "country_iso3": c.get("iso3"), "country_name": c.get("name"),
        "short_code": rec.get("shortCode"), "name": rec.get("name"), "legal_name": rec.get("legalName"),
        "commercial_name": rec.get("commercialName"), "commercial_region": rec.get("commercialRegion"),
        "carrier_id": rec.get("carrierId"), "new_carrier_id": rec.get("newCarrierId"), "sap_code": rec.get("sapCode"),
        "start_date": rec.get("startDate"), "end_date": rec.get("endDate"),
        "ultimate_parent_account_id": rec.get("ultimateParentAccountId"), "parent_account_id": rec.get("parentAccountId"),
        "identifier_number": rec.get("identifierNumber"), "trade_register_number": rec.get("tradeRegisterNumber"),
        "vat_number": rec.get("vatNumber"),
        "hq_street": hq.get("street"), "hq_street_number": hq.get("streetNumber"), "hq_city": hq.get("city"),
        "hq_postal_code": hq.get("postalCode"), "hq_country_id": hc.get("id"),
        "hq_country_iso3": hc.get("iso3"), "hq_country_name": hc.get("name"), "hq_state": hq.get("state"),
        "hq_residence": hq.get("residence"), "hq_floor": hq.get("floor"),
        "account_type_commercial_customer": yn(at.get("commercialCustomer")),
        "account_type_commercial_supplier": yn(at.get("commercialSupplier")),
        "account_type_partner": yn(at.get("partner")),
        "account_type_eligible_customer_prospects": yn(at.get("eligibleCustomerProspects")),
        "account_type_capacity_buying_supplier": yn(at.get("capacityBuyingSupplier")),
        "account_type_numbering_plan": yn(at.get("numberingPlan")),
        "account_type_easy_connect": yn(at.get("easyConnect")),
        "commercial_tier": meta.get("commercialTier"), "commercial_segment": meta.get("commercialSegment"),
        "commercial_subsegment": meta.get("commercialSubsegment"),
        "src_extracted_at": extracted_at, "src_batch_id": batch_id,
    }


def flat_city(rec, batch_id, extracted_at):
    return {
        "country_id": rec.get("country", {}).get("id"),
        "city_id": rec.get("id"),
        "city_abbreviation": rec.get("abbreviation") or rec.get("cityAbbreviation"),
        "city_name": rec.get("name") or rec.get("cityName"),
        "normalized_name": rec.get("normalizedName") or rec.get("normalized"),
        "city_alias": rec.get("alias"),
        "src_extracted_at": extracted_at, "src_batch_id": batch_id,
    }


def flat_country(rec, batch_id, extracted_at):
    return {
        "country_id": rec.get("id"),
        "country_iso2": rec.get("countryIso2") or rec.get("iso2"),
        "country_iso3": rec.get("countryIso3") or rec.get("iso3"),
        "name": rec.get("name"),
        "geographical_region": rec.get("geographicalRegion"),
        "commercial_region": rec.get("commercialRegion"),
        "phone_code": rec.get("phoneCode"),
        "mcc": rec.get("mcc"),
        "src_extracted_at": extracted_at, "src_batch_id": batch_id,
    }
