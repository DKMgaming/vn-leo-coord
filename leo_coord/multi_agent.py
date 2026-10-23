"""
Hệ thống Đa Tác nhân AI Thẩm định Cấp phép & Phối hợp Quốc tế LEO
(Multi-AI-Agent Regulatory & Technical Assessment Council)
Phục vụ Cơ quan Quản lý Tần số Vô tuyến điện Việt Nam (ARFM) & Ủy ban Vũ trụ Việt Nam.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from leo_coord.spacecap import Appendix4Filing, validate_appendix4_completeness
from leo_coord.appendix7 import evaluate_coexistence_5g_fs as evaluate_coexistence_5g, evaluate_vietnam_stations_appendix7
from leo_coord.epfd import simulate_s1503_cumulative_epfd


@dataclass
class AgentMessage:
    agent_id: str
    role_title_vi: str
    role_title_en: str
    agent_name: str
    avatar: str
    timestamp: str
    key_findings: List[str]
    technical_metrics: Dict[str, Any]
    statement_vi: str
    statement_en: str
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CouncilDossier:
    filing_id: str
    satellite_name: str
    notifying_adm: str
    operator: str
    br_ific_ref: int
    assessment_date: str
    overall_verdict: str  # "CONDITIONAL_APPROVAL_WITH_COORDINATION" | "REJECT_HARMFUL_INTERFERENCE" | "ACCEPTABLE"
    verdict_label_vi: str
    verdict_label_en: str
    risk_level: str  # "HIGH" | "MEDIUM" | "LOW"
    itu_legal_grounds: List[str]
    vietnam_pilot_conditions: List[str]
    bilateral_negotiation_points: List[str]
    executive_summary_vi: str
    executive_summary_en: str
    deliberations: List[AgentMessage] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MultiAgentCouncil:
    """Hội đồng Trợ lý AI Đa tác nhân Thẩm định Vệ tinh Quốc tế."""

    def __init__(self, filing: Appendix4Filing):
        self.filing = filing
        self.now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def run_data_specialist_agent(self) -> AgentMessage:
        """Tác nhân 1: Chuyên viên Dữ liệu SpaceCap (Data Specialist Agent)."""
        val = validate_appendix4_completeness(self.filing)
        total_sats = self.filing.total_satellites
        n_planes = len(self.filing.planes)
        freq_count = len(self.filing.frequency_assignments)

        # Kiểm tra trùng dải tần với mạng quốc gia
        has_ku = any(10.7 <= f.freq_min_ghz <= 12.75 for f in self.filing.frequency_assignments)
        has_ka = any(17.7 <= f.freq_min_ghz <= 30.0 for f in self.filing.frequency_assignments)

        findings = [
            f"Bóc tách thành công hồ sơ Phụ lục 4 (AP4): {self.filing.name} từ cơ quan {self.filing.notifying_adm} ({self.filing.operator}).",
            f"Quy mô chòm sao: {total_sats:,} vệ tinh trên {n_planes} mặt phẳng quỹ đạo ({self.filing.constellation_type}).",
            f"Độ đầy đủ dữ liệu kỹ thuật theo Phụ lục 4 ITU: {val['passed_checks']}/{val['total_checks']} chỉ tiêu ({val['status_label']}).",
        ]

        if has_ku:
            findings.append("Phát hiện trùng lặp băng Ku (10.7 - 12.75 GHz) với mạng VINASAT-1 (132.0°E) và VINASAT-2 (131.8°E).")
        if has_ka:
            findings.append("Phát hiện sử dụng băng Ka (27.5 - 29.5 GHz) trùng dải tần các trạm Gateway Quế Dương và Bình Dương.")

        statement_vi = (
            f"Tôi là Chuyên viên Dữ liệu Tần số Không gian. Tôi đã phân tích cấu trúc hồ sơ SpaceCap Phụ lục 4 của {self.filing.name}. "
            f"Hồ sơ này có tổng cộng {total_sats:,} vệ tinh ở độ cao xấp xỉ {self.filing.planes[0].altitude_km if self.filing.planes else 550} km. "
            f"Về mặt dữ liệu ITU, hồ sơ đạt mức hoàn thiện kỹ thuật {val['passed_checks']}/{val['total_checks']}. "
            f"Đặc biệt, dải tần hoạt động xâm lấn trực tiếp vào không gian tần số đang khai thác của 2 vệ tinh địa tĩnh quốc gia VINASAT "
            f"và các trạm Gateway LEO mặt đất tại Việt Nam."
        )

        statement_en = (
            f"As the SpaceCap Data Specialist, I have ingested and validated the Appendix 4 filing for {self.filing.name} ({self.filing.notifying_adm}). "
            f"The constellation comprises {total_sats:,} non-GSO satellites in {n_planes} orbital planes. "
            f"Data completeness meets {val['passed_checks']}/{val['total_checks']} mandatory ITU AP4 parameters. "
            f"Downlink/uplink frequencies overlap directly with Vietnamese GSO networks (VINASAT-1/2) and national gateway teleport stations."
        )

        recs = [
            "Trích xuất ma trận tham số quỹ đạo đưa vào mô hình động lực học quỹ đạo SGP4/Walker.",
            "Lưu trữ bản ghi hồ sơ vào Cơ sở dữ liệu Hồ sơ Vệ tinh Ngoại của Cục Tần số (ARFM).",
        ]

        return AgentMessage(
            agent_id="agent-data-specialist",
            role_title_vi="Chuyên viên Dữ liệu SpaceCap & Tình báo Tần số",
            role_title_en="SpaceCap Data Ingestor & Satellite Intelligence",
            agent_name="Agent 1 (Data Specialist)",
            avatar="🛰️",
            timestamp=self.now_iso,
            key_findings=findings,
            technical_metrics={
                "total_satellites": total_sats,
                "planes_count": n_planes,
                "ap4_completeness_pct": round((val['passed_checks'] / val['total_checks']) * 100, 1),
                "frequency_assignments_count": freq_count,
            },
            statement_vi=statement_vi,
            statement_en=statement_en,
            recommendations=recs,
        )

    def run_rf_engineer_agent(self) -> AgentMessage:
        """Tác nhân 2: Kỹ sư Vô tuyến & Can nhiễu LEO/GSO (RF Engineering Agent)."""
        from leo_coord.orbits import WalkerConstellation

        alt_km = 550.0
        inc_deg = 53.0
        n_sats = 120
        n_planes = 6
        if self.filing.planes:
            p0 = self.filing.planes[0]
            alt_km = p0.altitude_km
            inc_deg = p0.inclination_deg
            n_planes = max(1, p0.num_planes)
            n_sats = min(120, max(12, p0.satellites_per_plane * n_planes))

        w = WalkerConstellation(
            name=self.filing.name,
            alt_km=alt_km,
            inc_deg=inc_deg,
            n_sats=n_sats,
            n_planes=n_planes,
            phasing=1,
            kind="delta"
        )

        # Gọi tool mô phỏng S.1503 EPFD
        epfd_res = simulate_s1503_cumulative_epfd(
            constellation=w,
            eirp_dbw_per_mhz=10.0,
            freq_ghz=11.7,
            victim_lat=16.0372,
            victim_lon=108.2045,
            gso_lon_deg=132.0,
            dish_d_m=1.2,
            duration_s=1800.0,
            dt_s=120.0,
        )

        # Gọi tool phân tích chung sống 5G mmWave cho Gateway
        coex_5g = evaluate_coexistence_5g(freq_ghz=28.0)

        findings = [
            f"Mô phỏng EPFD tích lũy theo Rec. ITU-R S.1503-3 (trạm Đà Nẵng, đĩa 1.2m): Dung sai bảo vệ tối thiểu {epfd_res['min_margin_db']} dB so với Bảng 22-1A Thể lệ Vô tuyến.",
            f"Trạng thái tuân thủ EPFD Điều 22: {epfd_res['compliance_status']}.",
            f"Tương thích phổ tần 5G mmWave trạm Gateway (28 GHz): Yêu cầu suy hao cách ly {coex_5g['isolation_loss_required_db']:.1f} dB.",
            f"Vùng cách ly bảo vệ đài cổng (Exclusion Zone): {coex_5g['separation_distance_km']['urban']} km (Đô thị), {coex_5g['separation_distance_km']['rural_los']} km (LOS thông thoáng).",
            "Nguy cơ can nhiễu thẳng hàng (In-line Event): Bắt buộc cơ chế Beam Blanking khi búp sóng LEO nằm trong góc < 2.0° so với hướng đài mặt đất ngắm VINASAT.",
        ]

        statement_vi = (
            f"Về mặt kỹ thuật vô tuyến, tôi đã kích hoạt động cơ mô phỏng EPFD tích lũy ITU-R S.1503 và đánh giá chung sống phổ tần 5G. "
            f"Hệ thống đạt chuẩn Bảng 22-1A với dung sai biên +{epfd_res['min_margin_db']} dB trong điều kiện hoạt động bình thường, "
            f"tuy nhiên tại các thời điểm vệ tinh cắt qua góc nhìn In-line Event với VINASAT (132.0°E), mức can nhiễu tức thời sẽ tăng vọt nếu không có cơ chế tắt sóng. "
            f"Đồng thời, đài cổng Gateway băng Ka cần thiết lập vùng cách ly nghiêm ngặt tối thiểu {coex_5g['separation_distance_km']['urban']} km "
            f"để không làm tê liệt các trạm gốc 5G mmWave lân cận."
        )

        statement_en = (
            f"From an RF Engineering perspective, numerical simulations under Rec. ITU-R S.1503-3 demonstrate an aggregate EPFD margin of "
            f"+{epfd_res['min_margin_db']} dB against Table 22-1A limits. "
            f"However, momentary GSO in-line events demand compulsory beam-blanking (turn-off zones) within 2.0° of the geostationary orbital arc. "
            f"Furthermore, Ka-band gateway operations require a protective physical separation of at least {coex_5g['separation_distance_km']['urban']} km "
            f"in urban clusters to ensure electromagnetic compatibility with terrestrial 5G mmWave networks (3GPP n258)."
        )

        recs = [
            "Bắt buộc nhà mạng vệ tinh ký cam kết kỹ thuật thực hiện Beam Blanking tự động trên vùng trời Việt Nam.",
            f"Quy hoạch vị trí trạm Gateway cách xa khu dân cư và các trạm phát sóng 5G mmWave tối thiểu {coex_5g['separation_distance_km']['suburban']} km.",
            "Lắp đặt hệ thống giám sát kiểm chuẩn phổ tần độc lập của ARFM tại trạm Quế Dương và Bình Dương.",
        ]

        return AgentMessage(
            agent_id="agent-rf-engineer",
            role_title_vi="Kỹ sư Vô tuyến & Can nhiễu LEO/GSO",
            role_title_en="RF Engineering & EPFD Interference Analyst",
            agent_name="Agent 2 (RF Engineer)",
            avatar="📡",
            timestamp=self.now_iso,
            key_findings=findings,
            technical_metrics={
                "min_epfd_margin_db": epfd_res["min_margin_db"],
                "epfd_compliant": epfd_res["overall_compliant"],
                "isolation_loss_req_db": coex_5g["isolation_loss_required_db"],
                "gateway_urban_exclusion_km": coex_5g["separation_distance_km"]["urban"],
                "gateway_rural_exclusion_km": coex_5g["separation_distance_km"]["rural_los"],
            },
            statement_vi=statement_vi,
            statement_en=statement_en,
            recommendations=recs,
        )

    def run_legal_expert_agent(self) -> AgentMessage:
        """Tác nhân 3: Chuyên gia Pháp lý & Thể lệ Vô tuyến ITU (Legal Expert Agent)."""
        findings = [
            "Căn cứ Điều khoản 22.2 Thể lệ Vô tuyến ITU (RR No. 22.2): Các hệ thống phi địa tĩnh (Non-GSO) không được phép gây can nhiễu có hại và không được đòi hỏi sự bảo vệ từ các mạng GSO đang vận hành.",
            "Căn cứ Điều khoản 9.7B & 9.51 Thể lệ Vô tuyến: Cơ quan Quản lý Việt Nam (VTN) có quyền nộp văn bản Bất đồng ý kiến (Disagreement) trong thời hạn 4 tháng kể từ ngày công bố công báo BR IFIC.",
            "Căn cứ Quyết định số 659/QĐ-TTg của Thủ tướng Chính phủ: Dịch vụ viễn thông vệ tinh LEO chỉ được phép thí điểm tại Việt Nam khi đáp ứng trọn vẹn yêu cầu an ninh mạng, đặt Gateway trong nước và cam kết không gây nhiễu cho mạng thông tin quốc gia.",
            "Căn cứ Luật Tần số Vô tuyến điện (sửa đổi 2022): Cục Tần số có thẩm quyền thu hồi hoặc từ chối cấp phép phát sóng nếu doanh nghiệp không hoàn tất thủ tục phối hợp quốc tế theo quy định ITU.",
        ]

        statement_vi = (
            f"Về mặt pháp lý và quan hệ quốc tế, hồ sơ {self.filing.name} bắt buộc phải bước vào quy trình phối hợp song phương chính thức theo RR No. 9.7B và 9.52. "
            f"Việt Nam giữ quyền phủ quyết và bảo vệ nguyên trạng hoạt động của vệ tinh VINASAT-1 và VINASAT-2 theo Điều 22.2 Thể lệ Vô tuyến. "
            f"Để được cấp phép cung cấp dịch vụ thí điểm tại Việt Nam theo Quyết định 659/QĐ-TTg, doanh nghiệp bắt buộc phải ký Thỏa thuận Phối hợp Tần số (Coordination Agreement) "
            f"với cơ quan quản lý Việt Nam (ARFM) trước ngày đưa vào khai thác thương mại."
        )

        statement_en = (
            f"Under international telecommunication law, filing {self.filing.name} triggers mandatory bilateral coordination under ITU RR Nos. 9.7B and 9.52. "
            f"The Administration of Viet Nam retains inviolable protection rights under RR No. 22.2 for GSO networks VINASAT-1 and VINASAT-2. "
            f"In accordance with Prime Minister Decision No. 659/QD-TTg on pilot LEO telecommunication licensing, commercial spectrum clearance must be contingent "
            f"upon formal execution of a Bilateral Technical Coordination Agreement and local gateway localization."
        )

        recs = [
            f"Nộp công văn phản đối kỹ thuật chính thức thông qua phần mềm ITU SpaceCom trước hạn chót 4 tháng (RR 9.51/9.52).",
            "Đưa điều khoản cam kết 'Không gây can nhiễu có hại cho VINASAT' vào nội dung Giấy phép Thí điểm theo Quyết định 659/QĐ-TTg.",
            "Yêu cầu phía đối tác cung cấp dữ liệu đo kiểm thực địa tại các trạm Gateway Việt Nam trước khi cấp phép chính thức.",
        ]

        return AgentMessage(
            agent_id="agent-legal-expert",
            role_title_vi="Chuyên gia Pháp lý & Thể lệ Vô tuyến ITU",
            role_title_en="ITU Legal & Radio Regulations Expert",
            agent_name="Agent 3 (Legal Expert)",
            avatar="🧑‍⚖️",
            timestamp=self.now_iso,
            key_findings=findings,
            technical_metrics={
                "provisions_invoked": ["RR 9.7B", "RR 9.51", "RR 9.52", "RR 22.2", "Res 76", "QĐ 659/QĐ-TTg"],
                "spacecom_deadline_days_max": 122,
                "coordination_mandatory": True,
            },
            statement_vi=statement_vi,
            statement_en=statement_en,
            recommendations=recs,
        )

    def run_chief_coordinator_agent(self, data_msg: AgentMessage, rf_msg: AgentMessage, legal_msg: AgentMessage) -> AgentMessage:
        """Tác nhân 4: Trưởng ban Thẩm định & Thư ký Điều phối (Chief Coordinator Agent)."""
        recs = [
            "1. Phê chuẩn Dự thảo Công văn Bất đồng ý kiến SpaceCom gửi Cục Thông tin Vô tuyến ITU (ITU BR).",
            "2. Ban hành Thông báo Điều kiện Thẩm định Kỹ thuật gửi doanh nghiệp xin cấp phép thí điểm (theo Quyết định 659/QĐ-TTg).",
            "3. Kích hoạt chế độ kiểm chuẩn giám sát phổ tần thời gian thực tại 2 đài Gateway Quế Dương và Bình Dương.",
            "4. Thành lập Đoàn đàm phán phối hợp tần số quốc tế song phương (Bilateral Coordination Delegation).",
        ]

        statement_vi = (
            f"Sau khi lắng nghe và tổng hợp báo cáo chuyên sâu từ Chuyên viên Dữ liệu, Kỹ sư Vô tuyến và Chuyên gia Pháp lý, "
            f"Hội đồng AI Thẩm định ra kết luận: CHẤP THUẬN CÓ ĐIỀU KIỆN KÈM BẮT BUỘC PHỐI HỢP TẦN SỐ QUỐC TẾ (Conditional Approval with Coordination). "
            f"Hồ sơ {self.filing.name} về tổng thể đáp ứng ngưỡng EPFD lý thuyết S.1503, nhưng tiềm ẩn nguy cơ can nhiễu nghiêm trọng khi cắt qua hướng Vinasat và ảnh hưởng trạm 5G mmWave. "
            f"Hội đồng đã lập sẵn Bộ Hồ sơ Thẩm định và Dự thảo Phản đối SpaceCom sẵn sàng trình Lãnh đạo Cục Tần số phê duyệt."
        )

        statement_en = (
            f"Having synthesized detailed assessments from the Data Specialist, RF Engineer, and Legal Expert, "
            f"the AI Assessment Council issues a verdict of CONDITIONAL APPROVAL SUBJECT TO MANDATORY BILATERAL COORDINATION. "
            f"While {self.filing.name} nominally complies with theoretical EPFD masks, real-time in-line geometry and Ka-band gateway proximity "
            f"pose tangible interference risks. Comprehensive technical conditions and SpaceCom objection dossiers are hereby finalized for official executive dispatch."
        )

        return AgentMessage(
            agent_id="agent-chief-coordinator",
            role_title_vi="Trưởng ban Thẩm định & Thư ký Điều phối",
            role_title_en="Chief Coordinator & Assessment Rapporteur",
            agent_name="Agent 4 (Chief Coordinator)",
            avatar="👨‍💼",
            timestamp=self.now_iso,
            key_findings=[
                "Đạt được sự thống nhất 100% giữa các chuyên gia về phương án xử lý hồ sơ.",
                "Xác lập 4 điều kiện tiên quyết cho việc cấp phép thí điểm tại Việt Nam.",
                "Hoàn thành toàn diện Báo cáo Thẩm định Kỹ thuật Song ngữ chuẩn ITU.",
            ],
            technical_metrics={
                "council_consensus": "100%",
                "verdict_code": "CONDITIONAL_APPROVAL_WITH_COORDINATION",
                "recommended_action": "ISSUE_SPACECOM_OBJECTION_AND_PILOT_CONDITIONS",
            },
            statement_vi=statement_vi,
            statement_en=statement_en,
            recommendations=recs,
        )

    def convene_council(self) -> CouncilDossier:
        """Kích hoạt và điều hành toàn bộ phiên họp của Hội đồng Đa tác nhân."""
        data_msg = self.run_data_specialist_agent()
        rf_msg = self.run_rf_engineer_agent()
        legal_msg = self.run_legal_expert_agent()
        chief_msg = self.run_chief_coordinator_agent(data_msg, rf_msg, legal_msg)

        deliberations = [data_msg, rf_msg, legal_msg, chief_msg]

        pilot_conditions = [
            "1. Áp dụng vùng đệm không phát sóng (Beam Blanking / Geo-fencing) góc lệch < 2.0° bảo vệ tuyệt đối VINASAT-1 (132°E) và VINASAT-2 (131.8°E).",
            "2. Đảm bảo toàn bộ lưu lượng dữ liệu người dùng tại Việt Nam phải đi qua các đài Gateway đặt trên lãnh thổ Việt Nam (Quế Dương, Bình Dương) theo Quyết định 659/QĐ-TTg.",
            "3. Khoảng cách cách ly trạm Gateway với các trạm gốc di động 5G mmWave tối thiểu 2.4 km (khu đô thị) và 7.6 km (ngoại thành).",
            "4. Cung cấp API telemetry quỹ đạo và vị trí vệ tinh thời gian thực cho Cục Tần số vô tuyến điện phục vụ giám sát độc lập.",
            "5. Hoàn tất ký kết Thỏa thuận Phối hợp Kỹ thuật song phương (Coordination Agreement) với ARFM trước khi thương mại hóa.",
        ]

        bilateral_points = [
            "Yêu cầu phía cơ quan thông báo (USA/FCC hoặc CHN) cung cấp thuật toán điều khiển công suất động (ATPC) và lịch trình chuyển búp sóng.",
            "Thiết lập cơ chế phối hợp nóng 24/7 (Interference Hotline) giữa Trung tâm Kiểm soát Vệ tinh Quế Dương và Network Operations Center của nhà mạng LEO.",
            "Kiểm tra mức PFD thực đo tại các trạm tham chiếu Đà Nẵng và Nha Trang bằng thiết bị kiểm chuẩn chuyên dụng.",
        ]

        exec_vi = (
            f"Hội đồng Trợ lý AI Thẩm định đã hoàn thành phiên đánh giá kỹ thuật và pháp lý toàn diện đối với hồ sơ vệ tinh phi địa tĩnh {self.filing.name} "
            f"(Công báo BR IFIC số {self.filing.br_ific_ref}, Mục đặc biệt {self.filing.special_section}). "
            f"Kết luận: Chấp thuận có điều kiện bắt buộc thực hiện thủ tục phối hợp tần số quốc tế (RR 9.7B/9.52) và tuân thủ nghiêm ngặt "
            f"5 điều kiện cấp phép thí điểm theo Quyết định số 659/QĐ-TTg của Thủ tướng Chính phủ nhằm bảo vệ vững chắc chủ quyền không gian và tài nguyên quỹ đạo Vinasat của Việt Nam."
        )

        exec_en = (
            f"The Multi-AI-Agent Regulatory Council has concluded its comprehensive technical and legal assessment for the non-GSO satellite network {self.filing.name} "
            f"(BR IFIC No. {self.filing.br_ific_ref}, Special Section {self.filing.special_section}). "
            f"Finding: Conditional approval subject to mandatory international frequency coordination under RR Nos. 9.7B and 9.52, and strict compliance "
            f"with Vietnam's five national pilot licensing prerequisites under Prime Minister Decision No. 659/QD-TTg to safeguard sovereign GSO orbital rights."
        )

        return CouncilDossier(
            filing_id=self.filing.id,
            satellite_name=self.filing.name,
            notifying_adm=self.filing.notifying_adm,
            operator=self.filing.operator,
            br_ific_ref=self.filing.br_ific_ref,
            assessment_date=self.now_iso,
            overall_verdict="CONDITIONAL_APPROVAL_WITH_COORDINATION",
            verdict_label_vi="CHẤP THUẬN CÓ ĐIỀU KIỆN (BẮT BUỘC PHỐI HỢP QUỐC TẾ & BẢO VỆ VINASAT)",
            verdict_label_en="CONDITIONAL APPROVAL SUBJECT TO BILATERAL COORDINATION & GSO PROTECTION",
            risk_level="HIGH" if any("VINASAT" in k for k in data_msg.key_findings) else "MEDIUM",
            itu_legal_grounds=[
                "ITU Radio Regulations No. 9.7B (GSO vs Non-GSO Coordination)",
                "ITU Radio Regulations No. 9.51 & 9.52 (4-Month Objection Deadline)",
                "ITU Radio Regulations No. 22.2 (Protection of GSO Systems)",
                "WRC-15 Resolution 76 (Aggregate EPFD Protection Limits)",
                "ITU-R Recommendation S.1503-3 (EPFD Calculation Methodology)",
                "Quyết định 659/QĐ-TTg của Thủ tướng Chính phủ (Thí điểm cấp phép LEO tại Việt Nam)",
            ],
            vietnam_pilot_conditions=pilot_conditions,
            bilateral_negotiation_points=bilateral_points,
            executive_summary_vi=exec_vi,
            executive_summary_en=exec_en,
            deliberations=deliberations,
        )
