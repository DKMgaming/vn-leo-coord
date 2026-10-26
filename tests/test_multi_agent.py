from leo_coord.spacecap import load_spacecap_samples
from leo_coord.multi_agent import MultiAgentCouncil, CouncilDossier


def test_convene_multi_agent_council_starlink():
    samples = load_spacecap_samples()
    starlink = next(s for s in samples if s.id == "starlink-gen2-ap4")
    council = MultiAgentCouncil(starlink)
    dossier = council.convene_council()

    assert isinstance(dossier, CouncilDossier)
    assert dossier.satellite_name == "STARLINK-GEN2-C-1"
    assert dossier.overall_verdict == "CONDITIONAL_APPROVAL_WITH_COORDINATION"
    assert len(dossier.deliberations) == 4

    roles = [m.agent_id for m in dossier.deliberations]
    assert "agent-data-specialist" in roles
    assert "agent-rf-engineer" in roles
    assert "agent-legal-expert" in roles
    assert "agent-chief-coordinator" in roles

    rf_msg = next(m for m in dossier.deliberations if m.agent_id == "agent-rf-engineer")
    assert "min_epfd_margin_db" in rf_msg.technical_metrics
    assert rf_msg.technical_metrics["min_epfd_margin_db"] > 0
    assert rf_msg.technical_metrics["isolation_loss_req_db"] > 100

    assert len(dossier.vietnam_pilot_conditions) >= 4
    assert len(dossier.itu_legal_grounds) >= 5
    assert "659/QĐ-TTg" in dossier.executive_summary_vi


def test_convene_multi_agent_council_guowang():
    samples = load_spacecap_samples()
    guowang = next(s for s in samples if s.id == "guowang-gw-a59-ap4")
    council = MultiAgentCouncil(guowang)
    dossier = council.convene_council()

    assert dossier.satellite_name == "GW-A59"
    assert dossier.notifying_adm == "CHN"
    assert len(dossier.bilateral_negotiation_points) >= 3
    assert len(dossier.deliberations) == 4


def test_convene_multi_agent_council_itu_realtime_safe():
    from leo_coord.spacecap import get_filing_by_id
    korsat = get_filing_by_id("KORSAT-NGSO-KA")
    assert korsat is not None
    assert korsat.br_ific_ref == 3013
    council = MultiAgentCouncil(korsat)
    dossier = council.convene_council()

    assert dossier.overall_verdict == "PASS_NO_OBJECTION_NEEDED"
    assert dossier.risk_level == "LOW"
    assert "AN TOÀN" in dossier.verdict_label_vi
    assert len(dossier.deliberations) == 4


def test_convene_multi_agent_council_itu_realtime_high_risk():
    from leo_coord.spacecap import get_filing_by_id
    starlink_itu = get_filing_by_id("USASAT-NGSO-3-MOD")
    assert starlink_itu is not None
    assert starlink_itu.br_ific_ref == 3014
    council = MultiAgentCouncil(starlink_itu)
    dossier = council.convene_council()

    assert dossier.overall_verdict == "CONDITIONAL_APPROVAL_WITH_COORDINATION"
    assert dossier.risk_level == "HIGH"
    assert "CHẤP THUẬN CÓ ĐIỀU KIỆN" in dossier.verdict_label_vi
    assert len(dossier.vietnam_pilot_conditions) >= 5

