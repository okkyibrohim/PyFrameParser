import logging
import random
from typing import Dict, List, Optional

from allennlp.data.samplers import BatchSampler, MaxTokensBatchSampler

logger = logging.getLogger("mix_sampler")


@BatchSampler.register("mix_sampler")
class MixSampler(MaxTokensBatchSampler):
    def __init__(
        self,
        max_tokens: int,
        sorting_keys: Optional[List[str]] = None,
        padding_noise: float = 0.1,
        sampling_ratios: Optional[Dict[str, float]] = None,
    ):
        super().__init__(max_tokens, sorting_keys, padding_noise)  # type: ignore

        self.sampling_ratios = sampling_ratios or dict()

    def __iter__(self):
        indices, lengths = self._argsort_by_padding(self.data_source)

        original_num = len(indices)
        instance_types = [
            ins.fields["meta"].metadata.get("type", "default")
            if "meta" in ins.fields
            else "default"
            for ins in self.data_source
        ]
        instance_thresholds = [
            self.sampling_ratios[ins_type] if ins_type in self.sampling_ratios else 1.0
            for ins_type in instance_types
        ]
        for idx, threshold in enumerate(instance_thresholds):
            if random.random() > threshold:
                # Reject
                list_idx = indices.index(idx)
                del indices[list_idx], lengths[list_idx]
        if original_num != len(indices):
            logger.info(f"#instances reduced from {original_num} to {len(indices)}.")

        max_lengths = [max(length) for length in lengths]
        group_iterator = self._lazy_groups_of_max_size(indices, max_lengths)

        batches = [list(group) for group in group_iterator]
        random.shuffle(batches)
        for batch in batches:
            yield batch
