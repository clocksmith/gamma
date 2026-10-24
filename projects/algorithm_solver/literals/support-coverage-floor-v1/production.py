"""Exact shared-pool identity and supplied forward-reachability kernel."""
import coverage


def execute(inputs,expected):
    alphabet=set(chr(i) for i in range(32,127))|{'\n'}
    assert alphabet<=set(inputs['pool']) and not set(inputs['pool'])&set(inputs['banned'])
    assert all(set(text)<=alphabet for text in inputs['texts'].values())
    result=coverage.production(inputs['texts'],inputs['pool'],inputs['banned'])
    assert len(inputs['pool'])==expected['old_pool_entries']
    assert result['occurrences']==expected['old_occurrences']
    assert result['occurrence_sha256']==expected['old_occurrence_order_sha256']
    assert len(result['shared_entry_ids'])==expected['class_counts']['2']
    assert len(result['source_success'])==expected['fit_problems']
    assert sum(map(len,inputs['texts'].values()))==expected['geometry']['source_characters']
    assert result['forced_source_ids']==result['private_character_source_ids']
    return result
