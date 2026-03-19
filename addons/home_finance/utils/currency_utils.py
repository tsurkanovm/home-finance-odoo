
def compute_base_amount(record, model) -> float:
    if record.amount and record.currency_id and record.base_currency_id:
        return model.env['res.currency'].browse(record.currency_id.id)._convert(
            record.amount,
            record.base_currency_id,
            model.env.company,
            record.period
        )
    else:
        return 0.0