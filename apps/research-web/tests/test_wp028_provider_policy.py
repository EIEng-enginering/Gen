from app.research.general_provider_policy import assess,PROVIDERS

def test_public_sites_never_execute():
    for name in PROVIDERS:
        if name!='user_owned_export':
            assert assess(name,'search')['permitted'] is False
            assert assess(name,'search',permission_id='unverified',authorised_cost_cents=100)['permitted'] is False

def test_private_file_requires_separate_review():
    assert assess('user_owned_export','inspect_local_file')['permitted']
    assert not assess('user_owned_export','crawl')['permitted']
    assert not assess('new_unapproved_provider','search')['permitted']
