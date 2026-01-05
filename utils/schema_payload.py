def _iter_fields(detail):
    forms = detail.get("forms")
    if forms:
        for form in forms:
            for panel in form.get("panels", []):
                for group in panel.get("field_groups", []):
                    for field in group.get("fields", []):
                        yield field
        return

    panels = detail.get("panels")
    if panels:
        for panel in panels:
            for group in panel.get("field_groups", []):
                for field in group.get("fields", []):
                    yield field
        return


# ------------------------------------------------------
# SAFE FLOAT CONVERTER (fixes the crash)
# ------------------------------------------------------
def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        
        return 0.0


def _resolve_calc_value(row, context):
    field_calculate = row.get("field_calculate")
    key_calculate = row.get("key_calculate")
    BASE_value = row.get("BASE_value")

    if field_calculate:
        return _safe_float(context.get(field_calculate, 0))

    if key_calculate:
        return _safe_float(context.get(key_calculate, 0))

    if BASE_value not in (None, ""):
        return _safe_float(BASE_value)

    return 0.0


def compute_key_calculates(field_code, key_calculates, context):
    rows = sorted(key_calculates, key=lambda x: x.get("key_calculate_order", 0))

    total = 0.0
    started = False  
    
    for row in rows:
        sign = (row.get("calculate_sign") or "plus").lower()
        val = _resolve_calc_value(row, context)

        # Initialize on first value:
        if not started:
            if sign in ("multiply", "divide"):
                total = val
            else:
                total = val 
            started = True
            continue

        if sign == "plus":
            total += val
        elif sign == "minus":
            total -= val
        elif sign == "multiply":
            total *= val
        elif sign == "divide":
            if val != 0:
                total /= val

    return round(total, 2)


def build_payload(detail, value_resolver, rdm=None):
    if rdm is None:
        rdm = {}

    payload = []

    context = dict(rdm)
    generated_values = {}

    for field in _iter_fields(detail):
        code = field.get("code")
        key_calculates = field.get("key_calculates") or []

        if not code:
            continue

        # Case 1: calculated field
        if key_calculates:
            if code in generated_values:
                value = generated_values[code]
            else:
                value = compute_key_calculates(code, key_calculates, context)
                generated_values[code] = value

            context[code] = value
            payload.append({"field_code": code, "value": value, "comment": None})
            continue

        # Case 2: non-calculated field
        if code in generated_values:
            value = generated_values[code]
        else:
            if code in rdm:
                value = rdm[code]   
            else:
                value = value_resolver(field, context)

            generated_values[code] = value

        context[code] = value

        payload.append(
            {
                "field_code": code,
                "value": value,
                "comment": None,
            }
        )

    return payload
