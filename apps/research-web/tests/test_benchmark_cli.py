"""Scores are not probabilities; screening must reject bad/leaking inputs."""
import subprocess
from pathlib import Path
import pytest
from tools.evaluate_matching import read_cases, main


def write(path,rows):
    path.write_text('score,true_match,family_group,original_source_group,century,county\n'+rows,encoding='utf-8')


def test_cli_valid_heldout_is_report_only(tmp_path,capsys):
    train=tmp_path/'train.csv';hold=tmp_path/'hold.csv'
    write(train,'0.8,true,one,source-a,19,Kent\n')
    write(hold,'0.9,true,two,source-b,19,Essex\n0.2,false,three,source-c,18,Kent\n')
    out=tmp_path/'audit.json'
    assert main(['--train',str(train),'--holdout',str(hold),'--output',str(out)])==0
    content=out.read_text()
    assert '"may_deploy_calibrated_probabilities": false' in content
    assert '"tp": 1' in content


def test_leaked_family_is_rejected(tmp_path):
    train=tmp_path/'train.csv';hold=tmp_path/'hold.csv'
    write(train,'0.8,true,same,source-a,19,Kent\n')
    write(hold,'0.2,false,same,source-b,18,Essex\n')
    with pytest.raises(ValueError,match='Leaked family_group'):
        main(['--train',str(train),'--holdout',str(hold)])


def test_invalid_truth_label_nan_and_missing_fields_rejected(tmp_path):
    p=tmp_path/'bad.csv'
    write(p,'NaN,true,family,source-a,19,Kent\n')
    with pytest.raises(ValueError,match='score must be finite'):
        read_cases(p)
    write(p,'0.5,maybe,family,source-a,19,Kent\n')
    with pytest.raises(ValueError,match='true_match'):
        read_cases(p)
    p.write_text('name,score\na,0.9\n')
    with pytest.raises(ValueError,match='missing'):
        read_cases(p)
