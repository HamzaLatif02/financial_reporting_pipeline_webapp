"""
Marshmallow schemas for all API request/response bodies.
Used by flask-smorest to generate the OpenAPI 3.0 specification.
"""
from marshmallow import Schema, fields


# ── Assets ─────────────────────────────────────────────────────────────────

class AssetExampleSchema(Schema):
    symbol = fields.String()
    name   = fields.String()


class AssetCategorySchema(Schema):
    description = fields.String()
    examples    = fields.List(fields.Nested(AssetExampleSchema))


class CategoriesResponseSchema(Schema):
    categories = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(AssetCategorySchema),
    )


class PeriodItemSchema(Schema):
    value = fields.String()
    label = fields.String()


class PeriodsResponseSchema(Schema):
    periods = fields.List(fields.Nested(PeriodItemSchema))


class IntervalItemSchema(Schema):
    value = fields.String()
    label = fields.String()


class IntervalsResponseSchema(Schema):
    intervals = fields.List(fields.Nested(IntervalItemSchema))


class ValidateResponseSchema(Schema):
    valid = fields.Boolean()
    info  = fields.Dict(dump_default=None)
    error = fields.String(dump_default=None)


# ── Pipeline ───────────────────────────────────────────────────────────────

class SummaryStatsSchema(Schema):
    total_return_pct       = fields.Float(dump_default=None)
    annualised_return_pct  = fields.Float(dump_default=None)
    volatility_pct         = fields.Float(dump_default=None)
    sharpe_ratio           = fields.Float(dump_default=None)
    max_drawdown_pct       = fields.Float(dump_default=None)
    calmar_ratio           = fields.Float(dump_default=None)
    win_rate_pct           = fields.Float(dump_default=None)
    avg_monthly_return_pct = fields.Float(dump_default=None)


class LatestValueSchema(Schema):
    date  = fields.String()
    close = fields.Float(dump_default=None)


class PipelineRunResponseSchema(Schema):
    status        = fields.String()
    cache_hit     = fields.Boolean()
    cached_at     = fields.Float(dump_default=None)
    age_minutes   = fields.Float(dump_default=None)
    symbol        = fields.String()
    summary_stats = fields.Nested(SummaryStatsSchema)
    chart_urls    = fields.List(fields.String())
    latest_value  = fields.Nested(LatestValueSchema, dump_default=None)
    asset_info    = fields.Dict()


class AssetStatusRowSchema(Schema):
    symbol     = fields.String()
    name       = fields.String()
    asset_type = fields.String()
    run_at     = fields.String()
    row_count  = fields.Integer(dump_default=None)


class PipelineStatusResponseSchema(Schema):
    assets = fields.List(fields.Nested(AssetStatusRowSchema))


# ── Comparison ─────────────────────────────────────────────────────────────

class ComparisonRunResponseSchema(Schema):
    status       = fields.String()
    cache_hit    = fields.Boolean()
    cached_at    = fields.Float(dump_default=None)
    age_minutes  = fields.Float(dump_default=None)
    symbol_a     = fields.String()
    symbol_b     = fields.String()
    name_a       = fields.String()
    name_b       = fields.String()
    correlation  = fields.Float(dump_default=None)
    metrics      = fields.Dict()
    cum_returns  = fields.Dict()
    overlap_days = fields.Integer(dump_default=None)
    chart_urls   = fields.List(fields.String())
    pdf_url      = fields.String(dump_default=None)


# ── Schedule ───────────────────────────────────────────────────────────────

class ScheduleJobSchema(Schema):
    job_id        = fields.String()
    symbol        = fields.String()
    name          = fields.String()
    email         = fields.String()
    frequency     = fields.String()
    next_run_time = fields.String(dump_default=None)


class ScheduleListResponseSchema(Schema):
    jobs = fields.List(fields.Nested(ScheduleJobSchema))


class ScheduleAddResponseSchema(Schema):
    status  = fields.String()
    job_id  = fields.String()
    token   = fields.String()
    email   = fields.String()
    message = fields.String()


class ConfirmResponseSchema(Schema):
    status   = fields.String()
    symbol   = fields.String(dump_default=None)
    job_id   = fields.String()
    token    = fields.String()
    next_run = fields.String(dump_default=None)
    message  = fields.String()


class SendNowResponseSchema(Schema):
    status  = fields.String()
    symbol  = fields.String()
    email   = fields.String()
    message = fields.String()


class RemoveJobResponseSchema(Schema):
    status = fields.String()
    job_id = fields.String()


class PendingJobSchema(Schema):
    job_id    = fields.String()
    symbol    = fields.String()
    name      = fields.String()
    email     = fields.String()
    frequency = fields.String()
    hour      = fields.Integer()
    minute    = fields.Integer()


class PendingListResponseSchema(Schema):
    jobs = fields.List(fields.Nested(PendingJobSchema))


# ── Reports ────────────────────────────────────────────────────────────────

class ReportListResponseSchema(Schema):
    symbol  = fields.String()
    charts  = fields.List(fields.String())
    has_pdf = fields.Boolean()


# ── Cache ──────────────────────────────────────────────────────────────────

class CacheEntrySchema(Schema):
    symbol     = fields.String()
    name       = fields.String()
    period     = fields.String()
    interval   = fields.String()
    cached_at  = fields.Float()
    expires_at = fields.Float()
    expires_in = fields.String()


class CacheStatusResponseSchema(Schema):
    entries = fields.List(fields.Nested(CacheEntrySchema))
    count   = fields.Integer()


class CachePurgeResponseSchema(Schema):
    deleted = fields.Integer()
    message = fields.String()


class CacheInvalidateResponseSchema(Schema):
    status = fields.String()
    symbol = fields.String()


# ── Shared ─────────────────────────────────────────────────────────────────

class ErrorResponseSchema(Schema):
    error   = fields.String()
    status  = fields.String(dump_default=None)
    stage   = fields.String(dump_default=None)
    message = fields.String(dump_default=None)
