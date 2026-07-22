"""Retry policy (Dispatch 23, Workstream C10).

Bounded, recorded retries. A retry never overwrites an existing valid completed result.
"""
RETRYABLE = {"transient_network_failure", "worker_disconnect", "endpoint_timeout",
             "expired_lease", "controller_interruption"}
TERMINAL = {"invalid_generation_plan", "model_revision_mismatch", "prompt_hash_mismatch",
            "unsupported_required_parameter", "repeated_out_of_memory", "invalid_result_schema"}


class RetryPolicy:
    def __init__(self, policy_id="default", max_attempts=3):
        self.policy_id = policy_id
        self.max_attempts = max_attempts

    def classify(self, failure_kind):
        if failure_kind in TERMINAL:
            return "terminal"
        if failure_kind in RETRYABLE:
            return "retryable"
        return "retryable"    # unknown transient errors default to retryable but bounded

    def should_retry(self, attempt_count, failure_kind):
        return self.classify(failure_kind) == "retryable" and attempt_count < self.max_attempts

    def as_dict(self):
        return {"policy_id": self.policy_id, "max_attempts": self.max_attempts,
                "retryable_failures": sorted(RETRYABLE), "terminal_failures": sorted(TERMINAL)}
