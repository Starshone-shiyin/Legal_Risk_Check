"""Run lightweight project health checks for offline RAG governance tools.

The checks do not run full eval, call rag_query, contact Qdrant or an LLM, or
mutate retrieval, rerank, prompts, anchors, risk rules, eval cases, or hidden
seeds. The CLI writes one health report to the requested output path.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._shared.layout import compatibility_contract, resolve_report_pair


VERSION = "0.5.4"

DEFAULT_OUTPUT_PATH = Path("tests/project_health_check_report.json")

SYNTAX_CHECK_TARGETS = [
    Path("tools/check_encoding_hygiene.py"),
    Path("tools/export_api_contract_bundle.py"),
    Path("tools/export_api_field_catalog.py"),
    Path("tools/check_api_contract_consistency.py"),
    Path("tools/build_rag_evidence_independence_baseline.py"),
    Path("tools/build_rag_targeted_rerun_packet.py"),
    Path("tools/build_rag_expected_level_review_packet.py"),
    Path("tools/build_legal_text_version_verification_packet.py"),
    Path("tools/check_legal_corpus_integrity.py"),
    Path("tools/check_product_view_model_contract.py"),
    Path("tools/check_product_mock_endpoint_contract.py"),
    Path("tools/check_product_api_contract.py"),
    Path("tools/export_product_api_field_catalog.py"),
    Path("tools/export_product_api_status_catalog.py"),
    Path("tools/export_product_data_source_boundary.py"),
    Path("tools/build_product_backend_closeout.py"),
    Path("tools/check_tool_index_consistency.py"),
    Path("tools/check_test_index_consistency.py"),
    Path("tools/check_artifact_index_consistency.py"),
    Path("tools/check_layout_migration_readiness.py"),
    Path("tools/build_maintenance_closeout_report.py"),
    Path("tools/import_manual_review_workbench.py"),
    Path("tools/build_manual_review_export_pipeline_dry_run.py"),
    Path("tools/build_manual_review_visual_workbench.py"),
    Path("tools/build_pilot_manual_review_round1_support.py"),
    Path("tools/build_mobile_pilot_review_decision_aid.py"),
    Path("tools/build_ready_action_design_pack.py"),
    Path("tools/build_ready_action_design_review_brief.py"),
    Path("tools/check_ready_action_design_review_gate.py"),
    Path("tools/build_ready_action_design_review_worksheet.py"),
    Path("tools/build_ready_action_design_review_closeout.py"),
    Path("tools/build_ready_action_human_closeout_decision_draft.py"),
    Path("tools/build_ready_action_human_closeout_confirmation_record.py"),
    Path("tools/build_final_evidence_selection_policy_intake.py"),
    Path("tools/build_final_evidence_selection_policy_simulator_spec.py"),
    Path("tools/build_final_evidence_selection_policy_table_draft.py"),
    Path("tools/build_final_evidence_selection_policy_human_review_worksheet.py"),
    Path("tools/build_final_evidence_selection_policy_closeout_envelope.py"),
    Path("tools/build_final_evidence_selection_policy_closeout_decision_draft.py"),
    Path("tools/build_final_evidence_selection_policy_closeout_confirmation_record.py"),
    Path("tools/build_final_evidence_selection_policy_closeout_confirmed_record.py"),
    Path("tools/build_final_evidence_selection_policy_language_revision_worksheet.py"),
    Path("tools/build_final_evidence_selection_policy_language_revision_closeout_draft.py"),
    Path("tools/build_final_evidence_selection_policy_language_revision_confirmation_record.py"),
    Path("tools/build_final_evidence_selection_policy_offline_simulation_input_contract.py"),
    Path("tools/build_final_evidence_selection_policy_offline_simulation.py"),
    Path("tools/check_final_evidence_selection_policy_offline_simulation_gate.py"),
    Path("tools/build_final_evidence_selection_policy_adoption_decision_draft.py"),
    Path("tools/build_final_evidence_selection_policy_series_closeout.py"),
    Path("tools/build_retrieval_input_quality_intake.py"),
    Path("tools/build_retrieval_input_quality_audit_spec.py"),
    Path("tools/build_retrieval_input_quality_offline_audit.py"),
    Path("tools/check_retrieval_input_quality_offline_audit_gate.py"),
    Path("tools/build_retrieval_input_quality_diagnostic_prioritization.py"),
    Path("tools/check_retrieval_input_quality_diagnostic_prioritization_gate.py"),
    Path("tools/build_metadata_chunking_diagnostic_spec.py"),
    Path("tools/check_metadata_chunking_diagnostic_spec_gate.py"),
    Path("tools/build_metadata_chunking_diagnostic_runner_design.py"),
    Path("tools/check_metadata_chunking_diagnostic_runner_design_gate.py"),
    Path("tools/build_metadata_chunking_diagnostic_dry_run_contract.py"),
    Path("tools/build_retrieval_input_quality_series_closeout.py"),
    Path("tools/build_metadata_chunking_diagnostic_runner_manifest.py"),
    Path("tools/run_metadata_chunking_diagnostic_saved_report.py"),
    Path("tools/check_metadata_chunking_diagnostic_saved_report_runner_gate.py"),
    Path("tools/build_metadata_chunking_diagnostic_runner_series_closeout.py"),
    Path("tools/build_evidence_metadata_snapshot_contract.py"),
    Path("tools/run_evidence_metadata_snapshot.py"),
    Path("tools/check_evidence_metadata_snapshot_gate.py"),
    Path("tools/build_evidence_metadata_snapshot_series_closeout.py"),
    Path("tools/build_metadata_chunking_root_cause_report.py"),
    Path("tools/build_metadata_chunking_fix_design.py"),
    Path("tools/check_metadata_chunking_fix_design_gate.py"),
    Path("tools/build_metadata_chunking_series_closeout.py"),
    Path("tools/build_ingestion_metadata_patch_contract.py"),
    Path("tools/check_ingestion_metadata_patch_contract_gate.py"),
    Path("tools/build_ingestion_metadata_patch_dry_run_design.py"),
    Path("tools/check_ingestion_metadata_patch_dry_run_design_gate.py"),
    Path("tools/run_ingestion_metadata_patch_local_dry_run.py"),
    Path("tools/check_ingestion_metadata_patch_local_dry_run_gate.py"),
    Path("tools/build_ingestion_metadata_patch_actual_design.py"),
    Path("tools/check_ingestion_metadata_patch_actual_design_gate.py"),
    Path("tools/check_ingestion_metadata_source_patch.py"),
    Path("tools/build_ingestion_metadata_patch_post_patch_rebuild_dry_run_design.py"),
    Path("tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate.py"),
    Path("tools/run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py"),
    Path("tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate.py"),
    Path("tools/build_rebuild_authorization_design.py"),
    Path("tools/check_rebuild_authorization_design_gate.py"),
    Path("tools/build_human_rebuild_authorization_worksheet.py"),
    Path("tools/check_human_rebuild_authorization_worksheet_gate.py"),
    Path("tools/build_rebuild_runbook_preflight_contract.py"),
    Path("tools/build_ingestion_metadata_rebuild_planning_series_closeout.py"),
    Path("tools/build_production_rebuild_execution_design.py"),
    Path("tools/check_production_rebuild_execution_design_gate.py"),
    Path("tools/build_human_rebuild_authorization_record_scaffold.py"),
    Path("tools/check_human_rebuild_authorization_record_scaffold_gate.py"),
    Path("tools/build_human_rebuild_authorization_record_draft_design.py"),
    Path("tools/check_human_rebuild_authorization_record_draft_design_gate.py"),
    Path("tools/build_human_rebuild_authorization_record_draft_scaffold.py"),
    Path("tools/check_human_rebuild_authorization_record_draft_scaffold_gate.py"),
    Path("tools/build_human_rebuild_authorization_record_input_workflow_design.py"),
    Path("tools/check_human_rebuild_authorization_record_input_workflow_design_gate.py"),
    Path("tools/build_human_rebuild_authorization_record_input_packet_scaffold.py"),
    Path("tools/check_human_rebuild_authorization_record_input_packet_scaffold_gate.py"),
    Path("tools/build_human_rebuild_authorization_record_input_form_scaffold.py"),
    Path("tools/check_human_rebuild_authorization_record_input_form_scaffold_gate.py"),
    Path("tools/build_production_rebuild_readiness_cutoff.py"),
    Path("tools/build_production_rebuild_live_preflight_runner_design.py"),
    Path("tools/check_production_rebuild_live_preflight_runner_design_gate.py"),
    Path("tools/build_production_rebuild_live_preflight_runner_minimal_implementation_design.py"),
    Path("tools/check_production_rebuild_live_preflight_runner_minimal_implementation_design_gate.py"),
    Path("tools/build_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py"),
    Path("tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py"),
    Path("tools/run_production_rebuild_live_preflight.py"),
    Path("tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py"),
    Path("tools/run_production_rebuild_live_preflight_real_readonly_probe.py"),
    Path("tools/run_production_rebuild_live_preflight_snapshot_reference_probe.py"),
    Path("tools/run_production_rebuild_live_preflight_snapshot_create_reference_capture.py"),
    Path("tools/check_production_rebuild_formal_authorization_gate.py"),
    Path("tools/run_production_rebuild_execution.py"),
    Path("tools/check_production_rebuild_post_validation.py"),
    Path("tools/build_post_rebuild_quality_summary.py"),
    Path("tools/build_post_rebuild_rag_eval_summary.py"),
    Path("tools/build_post_rebuild_alignment_retention_delta.py"),
    Path("tools/build_production_rebuild_post_rebuild_series_closeout.py"),
    Path("tools/build_post_rebuild_repeat_stability_summary.py"),
    Path("tools/build_post_rebuild_repeat_instability_triage.py"),
    Path("tools/build_post_rebuild_final_evidence_drift_attribution.py"),
    Path("tools/build_post_rebuild_selection_trace_readiness.py"),
    Path("tools/build_post_rebuild_selection_trace_attribution.py"),
    Path("tools/build_post_rebuild_near_tie_stability_policy_design.py"),
    Path("tools/build_post_rebuild_near_tie_patch_validation.py"),
    Path("tools/build_post_rebuild_near_tie_patch_closeout.py"),
    Path("tools/build_rag_quality_triage.py"),
    Path("tools/build_dependency_trace_summary.py"),
    Path("tools/build_base_retrieval_query_inspection.py"),
    Path("tools/build_base_candidate_mismatch_summary.py"),
    Path("tools/build_base_candidate_live_readonly_probe.py"),
    Path("tools/build_base_candidate_dense_live_probe.py"),
    Path("tools/build_risk_level_overrisk_attribution.py"),
    Path("tools/build_risk_level_overrisk_legal_review_packet.py"),
    Path("src/rag/retriever.py"),
    Path("src/product/contracts.py"),
    Path("src/product/schemas.py"),
    Path("src/product/status.py"),
    Path("src/product/repository.py"),
    Path("src/product/service.py"),
    Path("src/product/router.py"),
    Path("tools/_shared/layout.py"),
    Path("src/main.py"),
]

REQUIRED_REPORTS = [
    Path("tests/encoding_hygiene_report.json"),
    Path("tests/tool_index_consistency_report.json"),
    Path("tests/test_index_consistency_report.json"),
    Path("tests/artifact_index_consistency_report.json"),
    Path("tests/layout_migration_readiness_report.json"),
    Path("tests/maintenance_closeout_report.json"),
    Path("tests/manual_review_visual_workbench_build_report.json"),
    Path("tests/manual_review_workbench_import_report.json"),
    Path("tests/pilot_manual_review_round1_support_report.json"),
    Path("tests/mobile_pilot_review_decision_aid_report.json"),
    Path("tests/manual_review_export_pipeline_dry_run_report.json"),
    Path("tests/manual_review_intake_gate_closeout_report.json"),
    Path("tests/ready_action_design_pack_report.json"),
    Path("tests/ready_action_design_review_brief_report.json"),
    Path("tests/ready_action_design_review_gate_report.json"),
    Path("tests/ready_action_design_review_worksheet_report.json"),
    Path("tests/ready_action_design_review_closeout_report.json"),
    Path("tests/ready_action_human_closeout_decision_draft_report.json"),
    Path("tests/ready_action_human_closeout_confirmation_record_report.json"),
    Path("tests/final_evidence_selection_policy_intake_report.json"),
    Path("tests/final_evidence_selection_policy_simulator_spec_report.json"),
    Path("tests/final_evidence_selection_policy_table_draft_report.json"),
    Path("tests/final_evidence_selection_policy_human_review_worksheet_report.json"),
    Path("tests/final_evidence_selection_policy_closeout_envelope_report.json"),
    Path("tests/final_evidence_selection_policy_closeout_decision_draft_report.json"),
    Path("tests/final_evidence_selection_policy_closeout_confirmation_record_report.json"),
    Path("tests/final_evidence_selection_policy_closeout_confirmed_record_report.json"),
    Path("tests/final_evidence_selection_policy_language_revision_worksheet_report.json"),
    Path("tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json"),
    Path("tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json"),
    Path("tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json"),
    Path("tests/final_evidence_selection_policy_offline_simulation_report.json"),
    Path("tests/final_evidence_selection_policy_offline_simulation_gate_report.json"),
    Path("tests/final_evidence_selection_policy_adoption_decision_draft_report.json"),
    Path("tests/final_evidence_selection_policy_series_closeout_report.json"),
    Path("tests/retrieval_input_quality_intake_report.json"),
    Path("tests/retrieval_input_quality_audit_spec_report.json"),
    Path("tests/retrieval_input_quality_offline_audit_report.json"),
    Path("tests/retrieval_input_quality_offline_audit_gate_report.json"),
    Path("tests/retrieval_input_quality_diagnostic_prioritization_report.json"),
    Path("tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json"),
    Path("tests/metadata_chunking_diagnostic_spec_report.json"),
    Path("tests/metadata_chunking_diagnostic_spec_gate_report.json"),
    Path("tests/metadata_chunking_diagnostic_runner_design_report.json"),
    Path("tests/metadata_chunking_diagnostic_runner_design_gate_report.json"),
    Path("tests/metadata_chunking_diagnostic_dry_run_contract_report.json"),
    Path("tests/retrieval_input_quality_series_closeout_report.json"),
    Path("tests/metadata_chunking_diagnostic_runner_manifest_report.json"),
    Path("tests/metadata_chunking_diagnostic_saved_report_runner_report.json"),
    Path("tests/metadata_chunking_diagnostic_saved_report_runner_gate_report.json"),
    Path("tests/metadata_chunking_diagnostic_runner_series_closeout_report.json"),
    Path("tests/evidence_metadata_snapshot_contract_report.json"),
    Path("tests/evidence_metadata_snapshot_report.json"),
    Path("tests/evidence_metadata_snapshot_gate_report.json"),
    Path("tests/evidence_metadata_snapshot_series_closeout_report.json"),
    Path("tests/metadata_chunking_root_cause_report.json"),
    Path("tests/metadata_chunking_fix_design_report.json"),
    Path("tests/metadata_chunking_fix_design_gate_report.json"),
    Path("tests/metadata_chunking_series_closeout_report.json"),
    Path("tests/ingestion_metadata_patch_contract_report.json"),
    Path("tests/ingestion_metadata_patch_contract_gate_report.json"),
    Path("tests/ingestion_metadata_patch_dry_run_design_report.json"),
    Path("tests/ingestion_metadata_patch_dry_run_design_gate_report.json"),
    Path("tests/ingestion_metadata_patch_local_dry_run_report.json"),
    Path("tests/ingestion_metadata_patch_local_dry_run_gate_report.json"),
    Path("tests/ingestion_metadata_patch_actual_design_report.json"),
    Path("tests/ingestion_metadata_patch_actual_design_gate_report.json"),
    Path("tests/ingestion_metadata_source_patch_report.json"),
    Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json"),
    Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json"),
    Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json"),
    Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json"),
    Path("tests/rebuild_authorization_design_report.json"),
    Path("tests/rebuild_authorization_design_gate_report.json"),
    Path("tests/human_rebuild_authorization_worksheet_report.json"),
    Path("tests/human_rebuild_authorization_worksheet_gate_report.json"),
    Path("tests/rebuild_runbook_preflight_contract_report.json"),
    Path("tests/ingestion_metadata_rebuild_planning_series_closeout_report.json"),
    Path("tests/production_rebuild_execution_design_report.json"),
    Path("tests/production_rebuild_execution_design_gate_report.json"),
    Path("tests/human_rebuild_authorization_record_scaffold_report.json"),
    Path("tests/human_rebuild_authorization_record_scaffold_gate_report.json"),
    Path("tests/human_rebuild_authorization_record_draft_design_report.json"),
    Path("tests/human_rebuild_authorization_record_draft_design_gate_report.json"),
    Path("tests/human_rebuild_authorization_record_draft_scaffold_report.json"),
    Path("tests/human_rebuild_authorization_record_draft_scaffold_gate_report.json"),
    Path("tests/human_rebuild_authorization_record_input_workflow_design_report.json"),
    Path("tests/human_rebuild_authorization_record_input_workflow_design_gate_report.json"),
    Path("tests/human_rebuild_authorization_record_input_packet_scaffold_report.json"),
    Path("tests/human_rebuild_authorization_record_input_packet_scaffold_gate_report.json"),
    Path("tests/human_rebuild_authorization_record_input_form_scaffold_report.json"),
    Path("tests/human_rebuild_authorization_record_input_form_scaffold_gate_report.json"),
    Path("tests/production_rebuild_readiness_cutoff_report.json"),
    Path("tests/production_rebuild_live_preflight_runner_design_report.json"),
    Path("tests/production_rebuild_live_preflight_runner_design_gate_report.json"),
    Path("tests/production_rebuild_live_preflight_runner_minimal_implementation_design_report.json"),
    Path("tests/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json"),
    Path("tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json"),
    Path("tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_report.json"),
    Path("tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json"),
    Path("tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_report.json"),
    Path("tests/production_rebuild_live_preflight_report.json"),
    Path("tests/production_rebuild_live_preflight_real_readonly_probe_report.json"),
    Path("tests/production_rebuild_live_preflight_snapshot_reference_probe_report.json"),
    Path("tests/production_rebuild_live_preflight_snapshot_create_reference_capture_report.json"),
    Path("tests/production_rebuild_formal_authorization_gate_report.json"),
    Path("tests/production_rebuild_authorization_record.json"),
    Path("tests/production_rebuild_execution_report.json"),
    Path("tests/production_rebuild_post_validation_report.json"),
    Path("tests/post_rebuild_smoke_eval_report.json"),
    Path("tests/post_rebuild_quality_summary_report.json"),
    Path("tests/post_rebuild_rag_eval_report.json"),
    Path("tests/post_rebuild_rag_eval_summary_report.json"),
    Path("tests/post_rebuild_rag_eval_after_alignment_retention_report.json"),
    Path("tests/post_rebuild_alignment_retention_delta_report.json"),
    Path("tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json"),
    Path("tests/production_rebuild_post_rebuild_series_closeout_report.json"),
    Path("tests/post_rebuild_repeat_full_rag_eval_v0.4.15.0_report.json"),
    Path("tests/post_rebuild_repeat_stability_summary_v0.4.15.0_report.json"),
    Path("tests/targeted_repeat_product_liability_v0.4.15.1_report.json"),
    Path("tests/targeted_repeat_algorithm_bias_v0.4.15.1_report.json"),
    Path("tests/post_rebuild_repeat_instability_triage_v0.4.15.1_report.json"),
    Path("tests/post_rebuild_final_evidence_drift_attribution_v0.4.15.2_report.json"),
    Path("tests/post_rebuild_selection_trace_readiness_v0.4.15.3_report.json"),
    Path("tests/targeted_repeat_algorithm_bias_trace_v0.4.15.4_report.json"),
    Path("tests/post_rebuild_selection_trace_attribution_v0.4.15.4_report.json"),
    Path("tests/post_rebuild_near_tie_stability_policy_design_v0.4.15.5_report.json"),
    Path("tests/targeted_repeat_algorithm_bias_near_tie_patch_v0.4.15.6_report.json"),
    Path("tests/post_rebuild_near_tie_patch_validation_v0.4.15.6_report.json"),
    Path("tests/post_rebuild_near_tie_patch_closeout_v0.4.15.7_report.json"),
    Path("tests/post_near_tie_patch_full_rag_eval_v0.4.15.8_report.json"),
    Path("tests/targeted_post_near_tie_regression_v0.4.15.8_report.json"),
    Path("tests/targeted_antitrust_risk_level_v0.4.15.8_report.json"),
    Path("tests/post_near_tie_patch_full_rag_eval_after_scope_fix_v0.4.15.8_report.json"),
    Path("tests/targeted_main_chain_stability_v0.4.15.9_report.json"),
    Path("tests/post_near_tie_main_chain_full_eval_v0.4.15.9_report.json"),
    Path("tests/targeted_data_export_answer_stability_v0.4.15.9_report.json"),
    Path("tests/targeted_data_export_term_preservation_v0.4.15.10_report.json"),
    Path("tests/targeted_main_chain_after_term_preservation_v0.4.15.10_report.json"),
    Path("tests/post_term_preservation_full_rag_eval_v0.4.15.10_report.json"),
    Path("tests/targeted_product_liability_term_preservation_v0.4.15.11_report.json"),
    Path("tests/targeted_output_stability_v0.4.15.11_report.json"),
    Path("tests/post_hidden_seed_signal_diag_v0.4.15.11_report.json"),
    Path("tests/targeted_same_bucket_baseline_v0.4.15.12_report.json"),
    Path("tests/post_same_bucket_baseline_full_rag_eval_v0.4.15.12_report.json"),
    Path("tests/post_same_bucket_signal_calibration_full_rag_eval_v0.4.15.12_report.json"),
    Path("tests/targeted_employee_facial_output_stability_v0.4.15.12_report.json"),
    Path("tests/targeted_compact_report_profile_v0.4.15.13_report.json"),
    Path("tests/post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json"),
    Path("tests/rag_quality_triage_v0.4.15.15_report.json"),
    Path("tests/targeted_dependency_trace_v0.4.15.16_report.json"),
    Path("tests/dependency_trace_summary_v0.4.15.16_report.json"),
    Path("tests/base_retrieval_query_inspection_v0.4.15.17_report.json"),
    Path("tests/base_candidate_mismatch_summary_v0.4.15.18_report.json"),
    Path("tests/base_candidate_live_readonly_probe_v0.4.15.19_report.json"),
    Path("tests/base_candidate_dense_live_probe_v0.4.15.20_report.json"),
    Path("tests/targeted_base_candidate_depth_patch_v0.4.15.21_report.json"),
    Path("tests/post_candidate_depth_patch_full_rag_eval_v0.4.15.21_report.json"),
    Path("tests/targeted_risk_level_exact_policy_v0.4.15.22_report.json"),
    Path("tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json"),
    Path("tests/risk_level_overrisk_attribution_v0.4.15.23_report.json"),
    Path("tests/risk_level_overrisk_legal_review_packet_v0.4.15.24_report.json"),
    Path("tests/targeted_trademark_overrisk_trace_v0.4.15.25_report.json"),
    Path("tests/targeted_trademark_overrisk_patch_v0.4.15.25_report.json"),
    Path("tests/post_trademark_overrisk_patch_full_rag_eval_v0.4.15.25_report.json"),
    Path("tests/targeted_process_overrisk_trace_v0.4.15.26_report.json"),
    Path("tests/targeted_process_overrisk_patch_v0.4.15.26_report.json"),
    Path("tests/targeted_trademark_overrisk_patch_v0.4.15.26_report.json"),
    Path("tests/targeted_vat_mixed_sales_patch_v0.4.15.26_report.json"),
    Path("tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json"),
    Path("tests/targeted_rag_evidence_independence_v0.4.17.3_report.json"),
    Path("tests/rag_expected_level_review_packet_v0.4.17.4_report.json"),
    Path("tests/legal_text_version_snapshot_v0.4.17.5.json"),
    Path("tests/legal_text_version_verification_packet_v0.4.17.5_report.json"),
    Path("tests/rag_expected_level_review_packet_v0.4.17.6_report.json"),
    Path("tests/legal_text_version_verification_packet_v0.4.17.6_report.json"),
    Path("tests/rag_eval_report_v0.4.17.7.json"),
    Path("tests/legal_corpus_integrity_v0.4.18.1_report.json"),
    Path("tests/product_view_model_contract_v0.4.18.3_report.json"),
    Path("tests/product_mock_endpoint_contract_v0.4.18.4_report.json"),
    Path("tests/product_api_contract_v0.4.18.5_report.json"),
    Path("tests/product_api_field_catalog_v0.4.18.6.json"),
    Path("tests/product_api_status_catalog_v0.4.18.7.json"),
    Path("tests/product_data_source_boundary_v0.4.18.8.json"),
    Path("tests/product_backend_closeout_v0.4.18.9_report.json"),
]

REQUIRED_SCAFFOLD_DIRECTORIES = [
    Path("reports"),
    Path("reports/eval"),
    Path("reports/audits"),
    Path("reports/manual_review"),
    Path("reports/dry_run"),
    Path("docs/indexes"),
    Path("docs/archive"),
    Path("tools/_shared"),
    Path("tools/eval"),
    Path("tools/evidence_diagnostics"),
    Path("tools/manual_review"),
    Path("tools/manual_review/workbench"),
    Path("tools/manual_review/pilot"),
    Path("tools/ops"),
    Path("tools/ingestion"),
]

ARTIFACT_INDEX_PATH = Path("docs/indexes/project_artifact_index.md")

ARTIFACT_INDEX_REQUIRED_ANCHORS = [
    "tests/encoding_hygiene_report.json",
    "tests/tool_index_consistency_report.json",
    "tests/test_index_consistency_report.json",
    "tests/artifact_index_consistency_report.json",
    "tests/layout_migration_readiness_report.json",
    "tests/maintenance_closeout_report.json",
    "tests/rag_eval_report.json",
    "tests/evidence_alignment_report.json",
    "tests/evidence_coverage_report.json",
    "tests/evidence_manual_review_workbench.json",
    "tests/manual_review_export_pipeline_dry_run_report.json",
    "tests/ready_action_design_pack_report.json",
    "tests/ready_action_design_review_brief_report.json",
    "tests/ready_action_design_review_gate_report.json",
    "tests/ready_action_design_review_worksheet_report.json",
    "tests/ready_action_design_review_closeout_report.json",
    "tests/ready_action_human_closeout_decision_draft_report.json",
    "tests/ready_action_human_closeout_confirmation_record_report.json",
    "tests/final_evidence_selection_policy_intake_report.json",
    "tests/final_evidence_selection_policy_simulator_spec_report.json",
    "tests/final_evidence_selection_policy_table_draft_report.json",
    "tests/final_evidence_selection_policy_human_review_worksheet_report.json",
    "tests/final_evidence_selection_policy_closeout_envelope_report.json",
    "tests/final_evidence_selection_policy_closeout_decision_draft_report.json",
    "tests/final_evidence_selection_policy_closeout_confirmation_record_report.json",
    "tests/final_evidence_selection_policy_closeout_confirmed_record_report.json",
    "tests/final_evidence_selection_policy_language_revision_worksheet_report.json",
    "tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json",
    "tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json",
    "tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json",
    "tests/final_evidence_selection_policy_offline_simulation_report.json",
    "tests/final_evidence_selection_policy_offline_simulation_gate_report.json",
    "tests/final_evidence_selection_policy_adoption_decision_draft_report.json",
    "tests/final_evidence_selection_policy_series_closeout_report.json",
    "tests/retrieval_input_quality_intake_report.json",
    "tests/retrieval_input_quality_audit_spec_report.json",
    "tests/retrieval_input_quality_offline_audit_report.json",
    "tests/retrieval_input_quality_offline_audit_gate_report.json",
    "tests/retrieval_input_quality_diagnostic_prioritization_report.json",
    "tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json",
    "tests/metadata_chunking_diagnostic_spec_report.json",
    "tests/metadata_chunking_diagnostic_spec_gate_report.json",
    "tests/metadata_chunking_diagnostic_runner_design_report.json",
    "tests/metadata_chunking_diagnostic_runner_design_gate_report.json",
    "tests/metadata_chunking_diagnostic_dry_run_contract_report.json",
    "tests/retrieval_input_quality_series_closeout_report.json",
    "tests/metadata_chunking_diagnostic_runner_manifest_report.json",
    "tests/metadata_chunking_diagnostic_saved_report_runner_report.json",
    "tests/metadata_chunking_diagnostic_saved_report_runner_gate_report.json",
    "tests/metadata_chunking_diagnostic_runner_series_closeout_report.json",
    "tests/evidence_metadata_snapshot_contract_report.json",
    "tests/evidence_metadata_snapshot_report.json",
    "tests/evidence_metadata_snapshot_gate_report.json",
    "tests/evidence_metadata_snapshot_series_closeout_report.json",
    "tests/metadata_chunking_root_cause_report.json",
    "tests/metadata_chunking_fix_design_report.json",
    "tests/metadata_chunking_fix_design_gate_report.json",
    "tests/metadata_chunking_series_closeout_report.json",
    "tests/ingestion_metadata_patch_contract_report.json",
    "tests/ingestion_metadata_patch_contract_gate_report.json",
    "tests/ingestion_metadata_patch_dry_run_design_report.json",
    "tests/ingestion_metadata_patch_dry_run_design_gate_report.json",
    "tests/ingestion_metadata_patch_local_dry_run_report.json",
    "tests/ingestion_metadata_patch_local_dry_run_gate_report.json",
    "tests/ingestion_metadata_patch_actual_design_report.json",
    "tests/ingestion_metadata_patch_actual_design_gate_report.json",
    "tests/ingestion_metadata_source_patch_report.json",
    "tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json",
    "tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json",
    "tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json",
    "tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json",
    "tests/rebuild_authorization_design_report.json",
    "tests/rebuild_authorization_design_gate_report.json",
    "tests/human_rebuild_authorization_worksheet_report.json",
    "tests/human_rebuild_authorization_worksheet_gate_report.json",
    "tests/rebuild_runbook_preflight_contract_report.json",
    "tests/ingestion_metadata_rebuild_planning_series_closeout_report.json",
    "docs/ingestion_metadata_rebuild_planning_series_closeout_v0.4.13.18.md",
    "tests/production_rebuild_execution_design_report.json",
    "docs/production_rebuild_execution_design_v0.4.14.0.md",
    "tests/production_rebuild_execution_design_gate_report.json",
    "docs/production_rebuild_execution_design_gate_v0.4.14.1.md",
    "tests/human_rebuild_authorization_record_scaffold_report.json",
    "docs/human_rebuild_authorization_record_scaffold_v0.4.14.2.md",
    "tests/human_rebuild_authorization_record_scaffold_gate_report.json",
    "docs/human_rebuild_authorization_record_scaffold_gate_v0.4.14.3.md",
    "tests/human_rebuild_authorization_record_draft_design_report.json",
    "docs/human_rebuild_authorization_record_draft_design_v0.4.14.4.md",
    "tests/human_rebuild_authorization_record_draft_design_gate_report.json",
    "docs/human_rebuild_authorization_record_draft_design_gate_v0.4.14.5.md",
    "tests/human_rebuild_authorization_record_draft_scaffold_report.json",
    "docs/human_rebuild_authorization_record_draft_scaffold_v0.4.14.6.md",
    "tests/human_rebuild_authorization_record_draft_scaffold_gate_report.json",
    "docs/human_rebuild_authorization_record_draft_scaffold_gate_v0.4.14.7.md",
    "tests/human_rebuild_authorization_record_input_workflow_design_report.json",
    "docs/human_rebuild_authorization_record_input_workflow_design_v0.4.14.8.md",
    "tests/human_rebuild_authorization_record_input_workflow_design_gate_report.json",
    "docs/human_rebuild_authorization_record_input_workflow_design_gate_v0.4.14.9.md",
    "tests/human_rebuild_authorization_record_input_packet_scaffold_report.json",
    "docs/human_rebuild_authorization_record_input_packet_scaffold_v0.4.14.10.md",
    "tests/human_rebuild_authorization_record_input_packet_scaffold_gate_report.json",
    "docs/human_rebuild_authorization_record_input_packet_scaffold_gate_v0.4.14.11.md",
    "tests/human_rebuild_authorization_record_input_form_scaffold_report.json",
    "docs/human_rebuild_authorization_record_input_form_scaffold_v0.4.14.12.md",
    "tests/human_rebuild_authorization_record_input_form_scaffold_gate_report.json",
    "docs/human_rebuild_authorization_record_input_form_scaffold_gate_v0.4.14.13.md",
    "tests/production_rebuild_readiness_cutoff_report.json",
    "docs/production_rebuild_readiness_cutoff_v0.4.14.14.md",
    "tests/production_rebuild_live_preflight_runner_design_report.json",
    "docs/production_rebuild_live_preflight_runner_design_v0.4.14.15.md",
    "tests/production_rebuild_live_preflight_runner_design_gate_report.json",
    "docs/production_rebuild_live_preflight_runner_design_gate_v0.4.14.16.md",
    "tests/production_rebuild_live_preflight_runner_minimal_implementation_design_report.json",
    "docs/production_rebuild_live_preflight_runner_minimal_implementation_design_v0.4.14.17.md",
    "tests/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json",
    "docs/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_v0.4.14.18.md",
    "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json",
    "docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_v0.4.14.19.md",
    "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_report.json",
    "docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_v0.4.14.20.md",
    "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json",
    "docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_v0.4.14.21.md",
    "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_report.json",
    "docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_v0.4.14.22.md",
    "tests/production_rebuild_live_preflight_report.json",
    "docs/production_rebuild_live_preflight_runner_v0.4.14.27.md",
    "docs/production_rebuild_authorization_record_intake_v0.4.14.28.md",
    "tests/production_rebuild_authorization_record.json",
    "tests/production_rebuild_execution_report.json",
    "docs/production_rebuild_execution_v0.4.14.29.md",
    "tests/production_rebuild_post_validation_report.json",
    "tests/post_rebuild_smoke_eval_report.json",
    "tests/post_rebuild_quality_summary_report.json",
    "docs/post_rebuild_quality_summary_v0.4.14.30.md",
    "tests/post_rebuild_rag_eval_report.json",
    "tests/post_rebuild_rag_eval_summary_report.json",
    "docs/post_rebuild_rag_eval_summary_v0.4.14.31.md",
    "tests/post_rebuild_rag_eval_after_alignment_retention_report.json",
    "docs/post_rebuild_alignment_retention_v0.4.14.32.md",
    "tests/post_rebuild_alignment_retention_delta_report.json",
    "docs/post_rebuild_alignment_retention_delta_v0.4.14.33.md",
    "tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json",
    "docs/post_rebuild_alignment_retention_tightening_v0.4.14.34.md",
    "tests/production_rebuild_post_rebuild_series_closeout_report.json",
    "docs/production_rebuild_post_rebuild_series_closeout_v0.4.14.35.md",
    "tests/post_rebuild_repeat_full_rag_eval_v0.4.15.0_report.json",
    "tests/post_rebuild_repeat_stability_summary_v0.4.15.0_report.json",
    "docs/post_rebuild_repeat_stability_summary_v0.4.15.0.md",
    "tests/targeted_repeat_product_liability_v0.4.15.1_report.json",
    "tests/targeted_repeat_algorithm_bias_v0.4.15.1_report.json",
    "tests/post_rebuild_repeat_instability_triage_v0.4.15.1_report.json",
    "docs/post_rebuild_repeat_instability_triage_v0.4.15.1.md",
    "tests/post_rebuild_final_evidence_drift_attribution_v0.4.15.2_report.json",
    "docs/post_rebuild_final_evidence_drift_attribution_v0.4.15.2.md",
    "tests/post_rebuild_selection_trace_readiness_v0.4.15.3_report.json",
    "docs/post_rebuild_selection_trace_readiness_v0.4.15.3.md",
    "tests/targeted_repeat_algorithm_bias_trace_v0.4.15.4_report.json",
    "tests/post_rebuild_selection_trace_attribution_v0.4.15.4_report.json",
    "docs/post_rebuild_selection_trace_attribution_v0.4.15.4.md",
    "tests/post_rebuild_near_tie_stability_policy_design_v0.4.15.5_report.json",
    "docs/post_rebuild_near_tie_stability_policy_design_v0.4.15.5.md",
    "tests/post_rebuild_near_tie_patch_validation_v0.4.15.6_report.json",
    "docs/post_rebuild_near_tie_patch_validation_v0.4.15.6.md",
    "tests/post_rebuild_near_tie_patch_closeout_v0.4.15.7_report.json",
    "docs/post_rebuild_near_tie_patch_closeout_v0.4.15.7.md",
    "tests/post_near_tie_patch_full_rag_eval_v0.4.15.8_report.json",
    "tests/targeted_post_near_tie_regression_v0.4.15.8_report.json",
    "tests/targeted_antitrust_risk_level_v0.4.15.8_report.json",
    "tests/post_near_tie_patch_full_rag_eval_after_scope_fix_v0.4.15.8_report.json",
    "docs/post_near_tie_patch_main_chain_repair_v0.4.15.8.md",
    "tests/targeted_main_chain_stability_v0.4.15.9_report.json",
    "tests/post_near_tie_main_chain_full_eval_v0.4.15.9_report.json",
    "tests/targeted_data_export_answer_stability_v0.4.15.9_report.json",
    "docs/post_near_tie_main_chain_stability_closeout_v0.4.15.9.md",
    "tests/targeted_data_export_term_preservation_v0.4.15.10_report.json",
    "tests/targeted_main_chain_after_term_preservation_v0.4.15.10_report.json",
    "tests/post_term_preservation_full_rag_eval_v0.4.15.10_report.json",
    "docs/standard_contract_term_preservation_v0.4.15.10.md",
    "tests/targeted_product_liability_term_preservation_v0.4.15.11_report.json",
    "tests/targeted_output_stability_v0.4.15.11_report.json",
    "tests/post_hidden_seed_signal_diag_v0.4.15.11_report.json",
    "tests/targeted_same_bucket_baseline_v0.4.15.12_report.json",
    "tests/post_same_bucket_baseline_full_rag_eval_v0.4.15.12_report.json",
    "tests/post_same_bucket_signal_calibration_full_rag_eval_v0.4.15.12_report.json",
    "tests/targeted_employee_facial_output_stability_v0.4.15.12_report.json",
    "tests/targeted_compact_report_profile_v0.4.15.13_report.json",
    "tests/post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json",
    "tests/rag_quality_triage_v0.4.15.15_report.json",
    "tests/targeted_dependency_trace_v0.4.15.16_report.json",
    "tests/dependency_trace_summary_v0.4.15.16_report.json",
    "tests/base_retrieval_query_inspection_v0.4.15.17_report.json",
    "tests/base_candidate_mismatch_summary_v0.4.15.18_report.json",
    "tests/base_candidate_live_readonly_probe_v0.4.15.19_report.json",
    "tests/base_candidate_dense_live_probe_v0.4.15.20_report.json",
    "tests/targeted_base_candidate_depth_patch_v0.4.15.21_report.json",
    "tests/post_candidate_depth_patch_full_rag_eval_v0.4.15.21_report.json",
    "tests/targeted_risk_level_exact_policy_v0.4.15.22_report.json",
    "tests/post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json",
    "tests/risk_level_overrisk_attribution_v0.4.15.23_report.json",
    "tests/risk_level_overrisk_legal_review_packet_v0.4.15.24_report.json",
    "tests/targeted_trademark_overrisk_trace_v0.4.15.25_report.json",
    "tests/targeted_trademark_overrisk_patch_v0.4.15.25_report.json",
    "tests/post_trademark_overrisk_patch_full_rag_eval_v0.4.15.25_report.json",
    "docs/trademark_overrisk_runtime_patch_v0.4.15.25.md",
    "tests/targeted_process_overrisk_trace_v0.4.15.26_report.json",
    "tests/targeted_process_overrisk_patch_v0.4.15.26_report.json",
    "tests/targeted_trademark_overrisk_patch_v0.4.15.26_report.json",
    "tests/targeted_vat_mixed_sales_patch_v0.4.15.26_report.json",
    "tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json",
    "docs/process_overrisk_runtime_hardening_v0.4.15.26.md",
    "docs/api_contract_stability_v0.4.16.1.md",
    "docs/api_error_and_export_contract_v0.4.16.2.md",
    "docs/openapi_schema_snapshot_v0.4.16.3.md",
    "tests/openapi_schema_v0.4.16.3.json",
    "docs/api_example_payloads_v0.4.16.4.md",
    "tests/fixtures/api_contract_example_payloads_v0.4.16.4.json",
    "docs/project_review_and_roadmap.md",
    "docs/final_report_version_guide.md",
    "docs/api_contract_bundle_v0.4.16.8.md",
    "docs/api_field_catalog_v0.4.16.10.md",
    "docs/api_contract_consistency_checker_v0.4.16.11.md",
    "docs/api_contract_stability_closeout_v0.4.16.12.md",
    "docs/rag_evidence_independence_baseline_v0.4.17.1.md",
    "docs/rag_targeted_rerun_packet_v0.4.17.2.md",
    "docs/rag_targeted_repeat_closeout_v0.4.17.3.md",
    "docs/rag_expected_level_review_packet_v0.4.17.4.md",
    "docs/legal_text_version_verification_packet_v0.4.17.5.md",
    "docs/unfair_competition_confusion_metadata_patch_v0.4.17.6.md",
    "docs/rag_full_eval_closeout_v0.4.17.7.md",
    "docs/legal_corpus_integrity_baseline_v0.4.18.1.md",
    "docs/product_design_brief_v0.4.18.2.md",
    "docs/product_view_model_contract_v0.4.18.3.md",
    "docs/product_mock_endpoint_contract_v0.4.18.4.md",
    "docs/product_api_backend_integration_v0.4.18.5.md",
    "docs/product_api_field_catalog_v0.4.18.6.md",
    "docs/product_api_status_catalog_v0.4.18.7.md",
    "docs/product_data_source_boundary_v0.4.18.8.md",
    "docs/product_backend_closeout_v0.4.18.9.md",
    "tests/api_contract_bundle_v0.4.16.9.json",
    "tests/api_field_catalog_v0.4.16.10.json",
    "tests/api_contract_consistency_v0.4.16.11_report.json",
    "tests/rag_evidence_independence_baseline_v0.4.17.1_report.json",
    "tests/rag_targeted_rerun_packet_v0.4.17.2_report.json",
    "tests/targeted_rag_evidence_independence_v0.4.17.3_report.json",
    "tests/rag_expected_level_review_packet_v0.4.17.4_report.json",
    "tests/legal_text_version_snapshot_v0.4.17.5.json",
    "tests/legal_text_version_verification_packet_v0.4.17.5_report.json",
    "tests/rag_expected_level_review_packet_v0.4.17.6_report.json",
    "tests/legal_text_version_verification_packet_v0.4.17.6_report.json",
    "tests/rag_eval_report_v0.4.17.7.json",
    "tests/legal_corpus_integrity_v0.4.18.1_report.json",
    "tests/fixtures/product_view_models_v0.4.18.3.json",
    "tests/product_view_model_contract_v0.4.18.3_report.json",
    "tests/product_mock_endpoint_contract_v0.4.18.4_report.json",
    "tests/product_api_contract_v0.4.18.5_report.json",
    "tests/product_api_field_catalog_v0.4.18.6.json",
    "tests/product_api_status_catalog_v0.4.18.7.json",
    "tests/product_data_source_boundary_v0.4.18.8.json",
    "tests/product_backend_closeout_v0.4.18.9_report.json",
    "docs/hidden_seed_signal_diagnostics_output_stability_v0.4.15.11.md",
    "tests/targeted_same_bucket_baseline_v0.4.15.12_report.json",
    "tests/post_same_bucket_baseline_full_rag_eval_v0.4.15.12_report.json",
    "tests/post_same_bucket_signal_calibration_full_rag_eval_v0.4.15.12_report.json",
    "tests/targeted_employee_facial_output_stability_v0.4.15.12_report.json",
    "docs/same_bucket_signal_calibration_v0.4.15.12.md",
    "docs/rag_eval_compact_report_profile_v0.4.15.13.md",
    "docs/roadmap_maintenance_compact_eval_baseline_v0.4.15.14.md",
    "docs/rag_quality_triage_v0.4.15.15.md",
    "docs/dependency_trace_summary_v0.4.15.16.md",
    "docs/base_retrieval_query_inspection_v0.4.15.17.md",
    "docs/base_candidate_mismatch_summary_v0.4.15.18.md",
    "docs/base_candidate_live_readonly_probe_v0.4.15.19.md",
    "docs/base_candidate_dense_live_probe_v0.4.15.20.md",
    "docs/base_candidate_depth_runtime_patch_v0.4.15.21.md",
    "docs/risk_level_exact_policy_v0.4.15.22.md",
    "docs/risk_level_overrisk_attribution_v0.4.15.23.md",
    "docs/risk_level_overrisk_legal_review_packet_v0.4.15.24.md",
    "docs/archive/project_review_and_roadmap_v0.4.15.13_snapshot.md",
    "tests/production_rebuild_live_preflight_real_readonly_probe_report.json",
    "docs/production_rebuild_live_preflight_real_readonly_probe_v0.4.14.23.md",
    "tests/production_rebuild_live_preflight_snapshot_reference_probe_report.json",
    "docs/production_rebuild_live_preflight_snapshot_reference_probe_v0.4.14.24.md",
    "tests/production_rebuild_live_preflight_snapshot_create_reference_capture_report.json",
    "docs/production_rebuild_live_preflight_snapshot_create_reference_capture_v0.4.14.25.md",
    "tests/production_rebuild_formal_authorization_gate_report.json",
    "docs/production_rebuild_formal_authorization_gate_v0.4.14.26.md",
    "tests/project_health_check_report.json",
    "reports/eval",
    "reports/manual_review",
]

TOOL_INDEX_PATH = Path("docs/indexes/project_tool_index.md")
TEST_INDEX_PATH = Path("docs/indexes/project_test_index.md")
MAINTENANCE_INDEX_PATH = Path("docs/indexes/project_maintenance_index.md")

TEST_INDEX_REQUIRED_ANCHORS = [
    "## 定位与约定",
    "## 测试套件",
    "## 测试产物",
    "tests/test_*.py",
    "tests/*.json",
    "tests/test_production_rebuild_execution_design.py",
    "tests/production_rebuild_execution_design_report.json",
    "production_rebuild_execution_design_gate",
    "human_rebuild_authorization_record_scaffold",
    "human_rebuild_authorization_record_scaffold_gate",
    "human_rebuild_authorization_record_draft_design",
    "human_rebuild_authorization_record_draft_design_gate",
    "human_rebuild_authorization_record_draft_scaffold",
    "human_rebuild_authorization_record_draft_scaffold_gate",
    "human_rebuild_authorization_record_input_workflow_design",
    "human_rebuild_authorization_record_input_workflow_design_gate",
    "human_rebuild_authorization_record_input_packet_scaffold",
    "human_rebuild_authorization_record_input_packet_scaffold_gate",
    "human_rebuild_authorization_record_input_form_scaffold",
    "human_rebuild_authorization_record_input_form_scaffold_gate",
    "production_rebuild_readiness_cutoff",
    "production_rebuild_live_preflight_runner_design",
    "production_rebuild_live_preflight_runner_design_gate",
    "production_rebuild_live_preflight_runner_minimal_implementation_design",
    "production_rebuild_live_preflight_runner_minimal_implementation_design_gate",
    "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design",
    "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate",
    "production_rebuild_live_preflight_runner_minimal_implementation_scaffold",
    "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate",
    "production_rebuild_live_preflight_real_readonly_probe",
    "production_rebuild_live_preflight_snapshot_reference_probe",
    "production_rebuild_live_preflight_snapshot_create_reference_capture",
    "production_rebuild_formal_authorization_gate",
    "production_rebuild_authorization_record",
    "production_rebuild_execution",
    "production_rebuild_post_validation",
    "post_rebuild_quality_summary",
    "post_rebuild_rag_eval_summary",
    "production_rebuild_post_rebuild_series_closeout",
    "post_rebuild_repeat_stability_summary",
    "post_rebuild_repeat_instability_triage",
    "post_rebuild_final_evidence_drift_attribution",
    "post_rebuild_selection_trace_readiness",
    "post_rebuild_selection_trace_attribution",
    "post_rebuild_near_tie_stability_policy_design",
    "post_rebuild_near_tie_patch_validation",
    "post_rebuild_near_tie_patch_closeout",
    "tests/test_base_candidate_mismatch_summary.py",
    "base_candidate_mismatch_summary",
    "tests/test_base_candidate_live_readonly_probe.py",
    "base_candidate_live_readonly_probe",
    "tests/test_base_candidate_dense_live_probe.py",
    "base_candidate_dense_live_probe",
    "tests/test_candidate_budget.py",
    "targeted_base_candidate_depth_patch_v0.4.15.21_report.json",
    "post_candidate_depth_patch_full_rag_eval_v0.4.15.21_report.json",
    "tests/test_rag_eval_diagnostics.py",
    "targeted_risk_level_exact_policy_v0.4.15.22_report.json",
    "post_risk_level_exact_policy_full_rag_eval_v0.4.15.22_report.json",
    "tests/test_risk_level_overrisk_attribution.py",
    "risk_level_overrisk_attribution_v0.4.15.23_report.json",
    "tests/test_risk_level_overrisk_legal_review_packet.py",
    "risk_level_overrisk_legal_review_packet_v0.4.15.24_report.json",
    "tests/test_retriever_contract.py",
    "targeted_trademark_overrisk_patch_v0.4.15.25_report.json",
    "post_trademark_overrisk_patch_full_rag_eval_v0.4.15.25_report.json",
    "targeted_process_overrisk_trace_v0.4.15.26_report.json",
    "targeted_process_overrisk_patch_v0.4.15.26_report.json",
    "targeted_trademark_overrisk_patch_v0.4.15.26_report.json",
    "targeted_vat_mixed_sales_patch_v0.4.15.26_report.json",
    "post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json",
    "tests/test_api_contract.py",
    "tests/test_api_contract_consistency.py",
    "tests/test_rag_evidence_independence_baseline.py",
    "tests/test_rag_targeted_rerun_packet.py",
    "tests/test_rag_expected_level_review_packet.py",
    "tests/test_legal_text_version_verification_packet.py",
    "tests/test_legal_corpus_integrity.py",
    "tests/test_product_view_model_contract.py",
    "tests/test_product_mock_endpoint_contract.py",
    "tests/test_product_api_contract.py",
    "tests/test_product_api_field_catalog.py",
    "tests/test_product_api_status_catalog.py",
    "tests/test_product_data_source_boundary.py",
    "tests/test_product_backend_closeout.py",
    "tests/test_roadmap_hygiene.py",
    "api_contract_bundle_v0.4.16.9.json",
    "api_field_catalog_v0.4.16.10.json",
    "api_contract_consistency_v0.4.16.11_report.json",
    "rag_evidence_independence_baseline_v0.4.17.1_report.json",
    "rag_targeted_rerun_packet_v0.4.17.2_report.json",
    "targeted_rag_evidence_independence_v0.4.17.3_report.json",
    "rag_expected_level_review_packet_v0.4.17.4_report.json",
    "legal_text_version_snapshot_v0.4.17.5.json",
    "legal_text_version_verification_packet_v0.4.17.5_report.json",
    "rag_expected_level_review_packet_v0.4.17.6_report.json",
    "legal_text_version_verification_packet_v0.4.17.6_report.json",
    "rag_eval_report_v0.4.17.7.json",
    "legal_corpus_integrity_v0.4.18.1_report.json",
    "product_view_models_v0.4.18.3.json",
    "product_view_model_contract_v0.4.18.3_report.json",
    "product_mock_endpoint_contract_v0.4.18.4_report.json",
    "product_api_contract_v0.4.18.5_report.json",
    "product_api_field_catalog_v0.4.18.6.json",
    "product_api_status_catalog_v0.4.18.7.json",
    "product_data_source_boundary_v0.4.18.8.json",
    "product_backend_closeout_v0.4.18.9_report.json",
    "openapi_schema_v0.4.16.3.json",
    "api_contract_example_payloads_v0.4.16.4.json",
    "tests/project_health_check_report.json",
    "tests/encoding_hygiene_report.json",
]

TOOL_INDEX_REQUIRED_ANCHORS = [
    "## 工具入口与产物关系",
    "tools/*.py",
    "tools/export_api_contract_bundle.py",
    "tools/export_api_field_catalog.py",
    "tools/check_api_contract_consistency.py",
    "tools/build_rag_evidence_independence_baseline.py",
    "tools/build_rag_targeted_rerun_packet.py",
    "tools/build_rag_expected_level_review_packet.py",
    "tools/build_legal_text_version_verification_packet.py",
    "tools/eval",
    "tools/evidence_diagnostics",
    "tools/manual_review",
    "tools/ops",
    "tools/ingestion",
    "scaffold",
    "tools/run_rag_eval.py",
    "tests/rag_eval_report.json",
    "tools/check_evidence_alignment.py",
    "tests/evidence_alignment_report.json",
    "tools/check_evidence_coverage.py",
    "tests/evidence_coverage_report.json",
    "tools/build_manual_review_visual_workbench.py",
    "tools/manual_review_visual_workbench/index.html",
    "tests/manual_review_visual_workbench_build_report.json",
    "tools/import_manual_review_workbench.py",
    "tests/manual_review_workbench_import_report.json",
    "tools/build_manual_review_export_pipeline_dry_run.py",
    "tests/manual_review_export_pipeline_dry_run_report.json",
    "tools/build_ready_action_design_pack.py",
    "tests/ready_action_design_pack_report.json",
    "tools/build_ready_action_design_review_brief.py",
    "tests/ready_action_design_review_brief_report.json",
    "tools/check_ready_action_design_review_gate.py",
    "tests/ready_action_design_review_gate_report.json",
    "tools/build_ready_action_design_review_worksheet.py",
    "tests/ready_action_design_review_worksheet_report.json",
    "tools/build_ready_action_design_review_closeout.py",
    "tests/ready_action_design_review_closeout_report.json",
    "tools/build_ready_action_human_closeout_decision_draft.py",
    "tests/ready_action_human_closeout_decision_draft_report.json",
    "tools/build_ready_action_human_closeout_confirmation_record.py",
    "tests/ready_action_human_closeout_confirmation_record_report.json",
    "tools/build_final_evidence_selection_policy_intake.py",
    "tests/final_evidence_selection_policy_intake_report.json",
    "tools/build_final_evidence_selection_policy_simulator_spec.py",
    "tests/final_evidence_selection_policy_simulator_spec_report.json",
    "tools/build_final_evidence_selection_policy_table_draft.py",
    "tests/final_evidence_selection_policy_table_draft_report.json",
    "tools/build_final_evidence_selection_policy_human_review_worksheet.py",
    "tests/final_evidence_selection_policy_human_review_worksheet_report.json",
    "tools/build_final_evidence_selection_policy_closeout_envelope.py",
    "tests/final_evidence_selection_policy_closeout_envelope_report.json",
    "tools/build_final_evidence_selection_policy_closeout_decision_draft.py",
    "tests/final_evidence_selection_policy_closeout_decision_draft_report.json",
    "tools/build_final_evidence_selection_policy_closeout_confirmation_record.py",
    "tests/final_evidence_selection_policy_closeout_confirmation_record_report.json",
    "tools/build_final_evidence_selection_policy_closeout_confirmed_record.py",
    "tests/final_evidence_selection_policy_closeout_confirmed_record_report.json",
    "tools/build_final_evidence_selection_policy_language_revision_worksheet.py",
    "tests/final_evidence_selection_policy_language_revision_worksheet_report.json",
    "tools/build_final_evidence_selection_policy_language_revision_closeout_draft.py",
    "tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json",
    "tools/build_final_evidence_selection_policy_language_revision_confirmation_record.py",
    "tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json",
    "tools/build_final_evidence_selection_policy_offline_simulation_input_contract.py",
    "tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json",
    "tools/build_final_evidence_selection_policy_offline_simulation.py",
    "tests/final_evidence_selection_policy_offline_simulation_report.json",
    "tools/check_final_evidence_selection_policy_offline_simulation_gate.py",
    "tests/final_evidence_selection_policy_offline_simulation_gate_report.json",
    "tools/build_final_evidence_selection_policy_adoption_decision_draft.py",
    "tests/final_evidence_selection_policy_adoption_decision_draft_report.json",
    "tools/build_final_evidence_selection_policy_series_closeout.py",
    "tests/final_evidence_selection_policy_series_closeout_report.json",
    "tools/build_retrieval_input_quality_intake.py",
    "tests/retrieval_input_quality_intake_report.json",
    "tools/build_retrieval_input_quality_audit_spec.py",
    "tests/retrieval_input_quality_audit_spec_report.json",
    "tools/build_retrieval_input_quality_offline_audit.py",
    "tests/retrieval_input_quality_offline_audit_report.json",
    "tools/check_retrieval_input_quality_offline_audit_gate.py",
    "tests/retrieval_input_quality_offline_audit_gate_report.json",
    "tools/build_retrieval_input_quality_diagnostic_prioritization.py",
    "tests/retrieval_input_quality_diagnostic_prioritization_report.json",
    "tools/check_retrieval_input_quality_diagnostic_prioritization_gate.py",
    "tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json",
    "tools/build_metadata_chunking_diagnostic_spec.py",
    "tests/metadata_chunking_diagnostic_spec_report.json",
    "tools/check_metadata_chunking_diagnostic_spec_gate.py",
    "tests/metadata_chunking_diagnostic_spec_gate_report.json",
    "tools/build_metadata_chunking_diagnostic_runner_design.py",
    "tests/metadata_chunking_diagnostic_runner_design_report.json",
    "tools/check_metadata_chunking_diagnostic_runner_design_gate.py",
    "tests/metadata_chunking_diagnostic_runner_design_gate_report.json",
    "tools/build_metadata_chunking_diagnostic_dry_run_contract.py",
    "tests/metadata_chunking_diagnostic_dry_run_contract_report.json",
    "tools/build_retrieval_input_quality_series_closeout.py",
    "tests/retrieval_input_quality_series_closeout_report.json",
    "tools/build_metadata_chunking_diagnostic_runner_manifest.py",
    "tests/metadata_chunking_diagnostic_runner_manifest_report.json",
    "tools/run_metadata_chunking_diagnostic_saved_report.py",
    "tests/metadata_chunking_diagnostic_saved_report_runner_report.json",
    "tools/check_metadata_chunking_diagnostic_saved_report_runner_gate.py",
    "tests/metadata_chunking_diagnostic_saved_report_runner_gate_report.json",
    "tools/build_metadata_chunking_diagnostic_runner_series_closeout.py",
    "tests/metadata_chunking_diagnostic_runner_series_closeout_report.json",
    "tools/build_evidence_metadata_snapshot_contract.py",
    "tests/evidence_metadata_snapshot_contract_report.json",
    "tools/run_evidence_metadata_snapshot.py",
    "tests/evidence_metadata_snapshot_report.json",
    "tools/check_evidence_metadata_snapshot_gate.py",
    "tests/evidence_metadata_snapshot_gate_report.json",
    "tools/build_evidence_metadata_snapshot_series_closeout.py",
    "tests/evidence_metadata_snapshot_series_closeout_report.json",
    "tools/build_metadata_chunking_root_cause_report.py",
    "tests/metadata_chunking_root_cause_report.json",
    "tools/build_metadata_chunking_fix_design.py",
    "tests/metadata_chunking_fix_design_report.json",
    "tools/check_metadata_chunking_fix_design_gate.py",
    "tests/metadata_chunking_fix_design_gate_report.json",
    "tools/build_metadata_chunking_series_closeout.py",
    "tests/metadata_chunking_series_closeout_report.json",
    "tools/build_ingestion_metadata_patch_contract.py",
    "tests/ingestion_metadata_patch_contract_report.json",
    "tools/check_ingestion_metadata_patch_contract_gate.py",
    "tests/ingestion_metadata_patch_contract_gate_report.json",
    "tools/build_ingestion_metadata_patch_dry_run_design.py",
    "tests/ingestion_metadata_patch_dry_run_design_report.json",
    "tools/check_ingestion_metadata_patch_dry_run_design_gate.py",
    "tests/ingestion_metadata_patch_dry_run_design_gate_report.json",
    "tools/run_ingestion_metadata_patch_local_dry_run.py",
    "tests/ingestion_metadata_patch_local_dry_run_report.json",
    "tools/check_ingestion_metadata_patch_local_dry_run_gate.py",
    "tests/ingestion_metadata_patch_local_dry_run_gate_report.json",
    "tools/build_ingestion_metadata_patch_actual_design.py",
    "tests/ingestion_metadata_patch_actual_design_report.json",
    "tools/check_ingestion_metadata_patch_actual_design_gate.py",
    "tests/ingestion_metadata_patch_actual_design_gate_report.json",
    "tools/check_ingestion_metadata_source_patch.py",
    "tests/ingestion_metadata_source_patch_report.json",
    "tools/build_ingestion_metadata_patch_post_patch_rebuild_dry_run_design.py",
    "tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json",
    "tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate.py",
    "tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json",
    "tools/run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py",
    "tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json",
    "tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate.py",
    "tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json",
    "tools/build_rebuild_authorization_design.py",
    "tests/rebuild_authorization_design_report.json",
    "tools/check_rebuild_authorization_design_gate.py",
    "tests/rebuild_authorization_design_gate_report.json",
    "tools/build_human_rebuild_authorization_worksheet.py",
    "tests/human_rebuild_authorization_worksheet_report.json",
    "tools/check_human_rebuild_authorization_worksheet_gate.py",
    "tests/human_rebuild_authorization_worksheet_gate_report.json",
    "tools/build_rebuild_runbook_preflight_contract.py",
    "tests/rebuild_runbook_preflight_contract_report.json",
    "tools/build_ingestion_metadata_rebuild_planning_series_closeout.py",
    "tests/ingestion_metadata_rebuild_planning_series_closeout_report.json",
    "tools/build_production_rebuild_execution_design.py",
    "tests/production_rebuild_execution_design_report.json",
    "tools/check_production_rebuild_execution_design_gate.py",
    "tests/production_rebuild_execution_design_gate_report.json",
    "tools/build_human_rebuild_authorization_record_scaffold.py",
    "tests/human_rebuild_authorization_record_scaffold_report.json",
    "tools/check_human_rebuild_authorization_record_scaffold_gate.py",
    "tests/human_rebuild_authorization_record_scaffold_gate_report.json",
    "tools/build_human_rebuild_authorization_record_draft_design.py",
    "tests/human_rebuild_authorization_record_draft_design_report.json",
    "tools/check_human_rebuild_authorization_record_draft_design_gate.py",
    "tests/human_rebuild_authorization_record_draft_design_gate_report.json",
    "tools/build_human_rebuild_authorization_record_draft_scaffold.py",
    "tests/human_rebuild_authorization_record_draft_scaffold_report.json",
    "tools/check_human_rebuild_authorization_record_draft_scaffold_gate.py",
    "tests/human_rebuild_authorization_record_draft_scaffold_gate_report.json",
    "tools/build_human_rebuild_authorization_record_input_workflow_design.py",
    "tests/human_rebuild_authorization_record_input_workflow_design_report.json",
    "tools/check_human_rebuild_authorization_record_input_workflow_design_gate.py",
    "tests/human_rebuild_authorization_record_input_workflow_design_gate_report.json",
    "tools/build_human_rebuild_authorization_record_input_packet_scaffold.py",
    "tests/human_rebuild_authorization_record_input_packet_scaffold_report.json",
    "tools/check_human_rebuild_authorization_record_input_packet_scaffold_gate.py",
    "tests/human_rebuild_authorization_record_input_packet_scaffold_gate_report.json",
    "tools/build_human_rebuild_authorization_record_input_form_scaffold.py",
    "tests/human_rebuild_authorization_record_input_form_scaffold_report.json",
    "tools/check_human_rebuild_authorization_record_input_form_scaffold_gate.py",
    "tests/human_rebuild_authorization_record_input_form_scaffold_gate_report.json",
    "tools/build_production_rebuild_readiness_cutoff.py",
    "tests/production_rebuild_readiness_cutoff_report.json",
    "tools/build_production_rebuild_live_preflight_runner_design.py",
    "tests/production_rebuild_live_preflight_runner_design_report.json",
    "tools/check_production_rebuild_live_preflight_runner_design_gate.py",
    "tests/production_rebuild_live_preflight_runner_design_gate_report.json",
    "tools/build_production_rebuild_live_preflight_runner_minimal_implementation_design.py",
    "tests/production_rebuild_live_preflight_runner_minimal_implementation_design_report.json",
    "tools/check_production_rebuild_live_preflight_runner_minimal_implementation_design_gate.py",
    "tests/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json",
    "tools/build_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py",
    "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json",
    "tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py",
    "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_report.json",
    "tools/run_production_rebuild_live_preflight.py",
    "tests/production_rebuild_live_preflight_report.json",
    "tests/production_rebuild_authorization_record.json",
    "tools/run_production_rebuild_execution.py",
    "tests/production_rebuild_execution_report.json",
    "tools/check_production_rebuild_post_validation.py",
    "tests/production_rebuild_post_validation_report.json",
    "tools/build_post_rebuild_quality_summary.py",
    "tests/post_rebuild_quality_summary_report.json",
    "tools/build_post_rebuild_rag_eval_summary.py",
    "tests/post_rebuild_rag_eval_summary_report.json",
    "tests/post_rebuild_rag_eval_after_alignment_retention_report.json",
    "tools/build_post_rebuild_alignment_retention_delta.py",
    "tests/post_rebuild_alignment_retention_delta_report.json",
    "tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json",
    "tools/build_production_rebuild_post_rebuild_series_closeout.py",
    "tests/production_rebuild_post_rebuild_series_closeout_report.json",
    "tools/build_post_rebuild_repeat_stability_summary.py",
    "tests/post_rebuild_repeat_stability_summary_v0.4.15.0_report.json",
    "tools/build_post_rebuild_repeat_instability_triage.py",
    "tests/post_rebuild_repeat_instability_triage_v0.4.15.1_report.json",
    "tools/build_post_rebuild_final_evidence_drift_attribution.py",
    "tests/post_rebuild_final_evidence_drift_attribution_v0.4.15.2_report.json",
    "tools/build_post_rebuild_selection_trace_readiness.py",
    "tests/post_rebuild_selection_trace_readiness_v0.4.15.3_report.json",
    "tools/build_post_rebuild_selection_trace_attribution.py",
    "tests/post_rebuild_selection_trace_attribution_v0.4.15.4_report.json",
    "tools/build_post_rebuild_near_tie_stability_policy_design.py",
    "tests/post_rebuild_near_tie_stability_policy_design_v0.4.15.5_report.json",
    "tools/build_post_rebuild_near_tie_patch_validation.py",
    "tests/post_rebuild_near_tie_patch_validation_v0.4.15.6_report.json",
    "tools/build_post_rebuild_near_tie_patch_closeout.py",
    "tools/build_rag_quality_triage.py",
    "tools/build_dependency_trace_summary.py",
    "tools/build_base_retrieval_query_inspection.py",
    "tools/build_base_candidate_mismatch_summary.py",
    "tools/build_base_candidate_live_readonly_probe.py",
    "tools/build_base_candidate_dense_live_probe.py",
    "tools/build_risk_level_overrisk_attribution.py",
    "tools/build_risk_level_overrisk_legal_review_packet.py",
    "tools/build_rag_targeted_rerun_packet.py",
    "tools/build_rag_expected_level_review_packet.py",
    "tools/build_legal_text_version_verification_packet.py",
    "tests/post_rebuild_near_tie_patch_closeout_v0.4.15.7_report.json",
    "tests/post_near_tie_patch_full_rag_eval_v0.4.15.8_report.json",
    "tests/targeted_post_near_tie_regression_v0.4.15.8_report.json",
    "tests/targeted_antitrust_risk_level_v0.4.15.8_report.json",
    "tests/post_near_tie_patch_full_rag_eval_after_scope_fix_v0.4.15.8_report.json",
    "tests/targeted_main_chain_stability_v0.4.15.9_report.json",
    "tests/post_near_tie_main_chain_full_eval_v0.4.15.9_report.json",
    "tests/targeted_data_export_answer_stability_v0.4.15.9_report.json",
    "tests/targeted_data_export_term_preservation_v0.4.15.10_report.json",
    "tests/targeted_main_chain_after_term_preservation_v0.4.15.10_report.json",
    "tests/post_term_preservation_full_rag_eval_v0.4.15.10_report.json",
    "tests/targeted_product_liability_term_preservation_v0.4.15.11_report.json",
    "tests/targeted_output_stability_v0.4.15.11_report.json",
    "tests/post_hidden_seed_signal_diag_v0.4.15.11_report.json",
    "tests/targeted_compact_report_profile_v0.4.15.13_report.json",
    "tests/post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json",
    "tests/rag_quality_triage_v0.4.15.15_report.json",
    "tests/targeted_dependency_trace_v0.4.15.16_report.json",
    "tests/dependency_trace_summary_v0.4.15.16_report.json",
    "tests/base_retrieval_query_inspection_v0.4.15.17_report.json",
    "tests/base_candidate_mismatch_summary_v0.4.15.18_report.json",
    "tests/base_candidate_live_readonly_probe_v0.4.15.19_report.json",
    "tests/base_candidate_dense_live_probe_v0.4.15.20_report.json",
    "tests/risk_level_overrisk_legal_review_packet_v0.4.15.24_report.json",
    "tests/targeted_trademark_overrisk_patch_v0.4.15.25_report.json",
    "tests/post_trademark_overrisk_patch_full_rag_eval_v0.4.15.25_report.json",
    "tests/targeted_process_overrisk_trace_v0.4.15.26_report.json",
    "tests/targeted_process_overrisk_patch_v0.4.15.26_report.json",
    "tests/targeted_trademark_overrisk_patch_v0.4.15.26_report.json",
    "tests/targeted_vat_mixed_sales_patch_v0.4.15.26_report.json",
    "tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json",
    "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json",
    "tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py",
    "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_report.json",
    "tools/run_production_rebuild_live_preflight_real_readonly_probe.py",
    "tests/production_rebuild_live_preflight_real_readonly_probe_report.json",
    "tools/run_production_rebuild_live_preflight_snapshot_reference_probe.py",
    "tests/production_rebuild_live_preflight_snapshot_reference_probe_report.json",
    "tools/run_production_rebuild_live_preflight_snapshot_create_reference_capture.py",
    "tests/production_rebuild_live_preflight_snapshot_create_reference_capture_report.json",
    "tools/check_production_rebuild_formal_authorization_gate.py",
    "tests/production_rebuild_formal_authorization_gate_report.json",
    "tools/check_encoding_hygiene.py",
    "tools/check_tool_index_consistency.py",
    "tools/check_test_index_consistency.py",
    "tools/check_artifact_index_consistency.py",
    "tools/run_project_health_check.py",
    "tests/project_health_check_report.json",
    "tools/check_ingestion_quality.py",
    "full eval",
    "rag_query",
    "Qdrant",
    "LLM",
]

SCAFFOLD_PURITY_ROOTS = [
    Path("reports/eval"),
    Path("reports/audits"),
    Path("reports/manual_review"),
    Path("reports/dry_run"),
    Path("docs/indexes"),
    Path("docs/archive"),
    Path("tools/_shared"),
    Path("tools/eval"),
    Path("tools/evidence_diagnostics"),
    Path("tools/manual_review"),
    Path("tools/ops"),
    Path("tools/ingestion"),
]

SCAFFOLD_ALLOWED_FILES = {
    Path("reports/eval/.gitkeep"),
    Path("reports/audits/.gitkeep"),
    Path("reports/manual_review/.gitkeep"),
    Path("reports/dry_run/.gitkeep"),
    Path("docs/indexes/project_structure_index.md"),
    Path("docs/indexes/project_artifact_index.md"),
    Path("docs/indexes/project_tool_index.md"),
    Path("docs/indexes/project_test_index.md"),
    Path("docs/indexes/project_maintenance_index.md"),
    Path("docs/maintenance_terms_guide.md"),
    Path("docs/archive/.gitkeep"),
    Path("docs/archive/project_review_and_roadmap_v0.4.15.13_snapshot.md"),
    Path("tools/_shared/README.md"),
    Path("tools/_shared/__init__.py"),
    Path("tools/_shared/layout.py"),
    Path("tools/eval/.gitkeep"),
    Path("tools/evidence_diagnostics/.gitkeep"),
    Path("tools/manual_review/workbench/.gitkeep"),
    Path("tools/manual_review/pilot/.gitkeep"),
    Path("tools/ops/.gitkeep"),
    Path("tools/ingestion/.gitkeep"),
}

ADVISORY_REPORTS = [
    Path("tests/pilot_manual_review_round1_support_report.json"),
    Path("tests/mobile_pilot_review_decision_aid_report.json"),
]

OFFLINE_TOOL_TARGETS = [
    Path("tools/check_legal_corpus_integrity.py"),
    Path("tools/check_product_view_model_contract.py"),
    Path("tools/check_product_mock_endpoint_contract.py"),
    Path("tools/check_product_api_contract.py"),
    Path("tools/export_product_api_field_catalog.py"),
    Path("tools/export_product_api_status_catalog.py"),
    Path("tools/export_product_data_source_boundary.py"),
    Path("tools/build_product_backend_closeout.py"),
    Path("tools/import_manual_review_workbench.py"),
    Path("tools/build_manual_review_export_pipeline_dry_run.py"),
    Path("tools/build_manual_review_visual_workbench.py"),
    Path("tools/build_pilot_manual_review_round1_support.py"),
    Path("tools/build_mobile_pilot_review_decision_aid.py"),
    Path("tools/build_ready_action_design_pack.py"),
    Path("tools/build_ready_action_design_review_brief.py"),
    Path("tools/check_ready_action_design_review_gate.py"),
    Path("tools/build_ready_action_design_review_worksheet.py"),
    Path("tools/build_ready_action_design_review_closeout.py"),
    Path("tools/build_ready_action_human_closeout_decision_draft.py"),
    Path("tools/build_ready_action_human_closeout_confirmation_record.py"),
    Path("tools/build_final_evidence_selection_policy_intake.py"),
    Path("tools/build_final_evidence_selection_policy_simulator_spec.py"),
    Path("tools/build_final_evidence_selection_policy_table_draft.py"),
    Path("tools/build_final_evidence_selection_policy_human_review_worksheet.py"),
    Path("tools/build_final_evidence_selection_policy_closeout_envelope.py"),
    Path("tools/build_final_evidence_selection_policy_closeout_decision_draft.py"),
    Path("tools/build_final_evidence_selection_policy_closeout_confirmation_record.py"),
    Path("tools/build_final_evidence_selection_policy_closeout_confirmed_record.py"),
    Path("tools/build_final_evidence_selection_policy_language_revision_worksheet.py"),
    Path("tools/build_final_evidence_selection_policy_language_revision_closeout_draft.py"),
    Path("tools/build_final_evidence_selection_policy_language_revision_confirmation_record.py"),
    Path("tools/build_final_evidence_selection_policy_offline_simulation_input_contract.py"),
    Path("tools/build_final_evidence_selection_policy_offline_simulation.py"),
    Path("tools/check_final_evidence_selection_policy_offline_simulation_gate.py"),
    Path("tools/build_final_evidence_selection_policy_adoption_decision_draft.py"),
    Path("tools/build_final_evidence_selection_policy_series_closeout.py"),
    Path("tools/build_retrieval_input_quality_intake.py"),
    Path("tools/build_retrieval_input_quality_audit_spec.py"),
    Path("tools/build_retrieval_input_quality_offline_audit.py"),
    Path("tools/check_retrieval_input_quality_offline_audit_gate.py"),
    Path("tools/build_retrieval_input_quality_diagnostic_prioritization.py"),
    Path("tools/check_retrieval_input_quality_diagnostic_prioritization_gate.py"),
    Path("tools/build_metadata_chunking_diagnostic_spec.py"),
    Path("tools/check_metadata_chunking_diagnostic_spec_gate.py"),
    Path("tools/build_metadata_chunking_diagnostic_runner_design.py"),
    Path("tools/check_metadata_chunking_diagnostic_runner_design_gate.py"),
    Path("tools/build_metadata_chunking_diagnostic_dry_run_contract.py"),
    Path("tools/build_retrieval_input_quality_series_closeout.py"),
    Path("tools/build_metadata_chunking_diagnostic_runner_manifest.py"),
    Path("tools/run_metadata_chunking_diagnostic_saved_report.py"),
    Path("tools/check_metadata_chunking_diagnostic_saved_report_runner_gate.py"),
    Path("tools/build_metadata_chunking_diagnostic_runner_series_closeout.py"),
    Path("tools/build_evidence_metadata_snapshot_contract.py"),
    Path("tools/check_evidence_metadata_snapshot_gate.py"),
    Path("tools/build_evidence_metadata_snapshot_series_closeout.py"),
    Path("tools/build_metadata_chunking_root_cause_report.py"),
    Path("tools/build_metadata_chunking_fix_design.py"),
    Path("tools/check_metadata_chunking_fix_design_gate.py"),
    Path("tools/build_metadata_chunking_series_closeout.py"),
    Path("tools/build_ingestion_metadata_patch_contract.py"),
    Path("tools/check_ingestion_metadata_patch_contract_gate.py"),
    Path("tools/build_ingestion_metadata_patch_dry_run_design.py"),
    Path("tools/check_ingestion_metadata_patch_dry_run_design_gate.py"),
    Path("tools/run_ingestion_metadata_patch_local_dry_run.py"),
    Path("tools/check_ingestion_metadata_patch_local_dry_run_gate.py"),
    Path("tools/build_ingestion_metadata_patch_actual_design.py"),
    Path("tools/check_ingestion_metadata_patch_actual_design_gate.py"),
    Path("tools/check_ingestion_metadata_source_patch.py"),
    Path("tools/build_ingestion_metadata_patch_post_patch_rebuild_dry_run_design.py"),
    Path("tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate.py"),
    Path("tools/run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py"),
    Path("tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate.py"),
    Path("tools/build_rebuild_authorization_design.py"),
    Path("tools/check_rebuild_authorization_design_gate.py"),
    Path("tools/build_human_rebuild_authorization_worksheet.py"),
    Path("tools/check_human_rebuild_authorization_worksheet_gate.py"),
    Path("tools/build_rebuild_runbook_preflight_contract.py"),
    Path("tools/build_ingestion_metadata_rebuild_planning_series_closeout.py"),
    Path("tools/build_production_rebuild_execution_design.py"),
    Path("tools/check_production_rebuild_execution_design_gate.py"),
    Path("tools/build_human_rebuild_authorization_record_scaffold.py"),
    Path("tools/check_human_rebuild_authorization_record_scaffold_gate.py"),
    Path("tools/build_human_rebuild_authorization_record_draft_design.py"),
    Path("tools/check_human_rebuild_authorization_record_draft_design_gate.py"),
    Path("tools/build_human_rebuild_authorization_record_draft_scaffold.py"),
    Path("tools/check_human_rebuild_authorization_record_draft_scaffold_gate.py"),
    Path("tools/build_human_rebuild_authorization_record_input_workflow_design.py"),
    Path("tools/check_human_rebuild_authorization_record_input_workflow_design_gate.py"),
    Path("tools/build_human_rebuild_authorization_record_input_packet_scaffold.py"),
    Path("tools/check_human_rebuild_authorization_record_input_packet_scaffold_gate.py"),
    Path("tools/build_human_rebuild_authorization_record_input_form_scaffold.py"),
    Path("tools/check_human_rebuild_authorization_record_input_form_scaffold_gate.py"),
    Path("tools/build_production_rebuild_readiness_cutoff.py"),
    Path("tools/build_production_rebuild_live_preflight_runner_design.py"),
    Path("tools/check_production_rebuild_live_preflight_runner_design_gate.py"),
    Path("tools/build_production_rebuild_live_preflight_runner_minimal_implementation_design.py"),
    Path("tools/check_production_rebuild_live_preflight_runner_minimal_implementation_design_gate.py"),
    Path("tools/build_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py"),
    Path("tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py"),
    Path("tools/run_production_rebuild_live_preflight.py"),
    Path("tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py"),
    Path("tools/run_production_rebuild_live_preflight_real_readonly_probe.py"),
    Path("tools/run_production_rebuild_live_preflight_snapshot_reference_probe.py"),
    Path("tools/run_production_rebuild_live_preflight_snapshot_create_reference_capture.py"),
    Path("tools/check_production_rebuild_formal_authorization_gate.py"),
    Path("tools/build_post_rebuild_repeat_stability_summary.py"),
    Path("tools/build_post_rebuild_repeat_instability_triage.py"),
    Path("tools/build_post_rebuild_final_evidence_drift_attribution.py"),
    Path("tools/build_post_rebuild_selection_trace_readiness.py"),
    Path("tools/build_post_rebuild_selection_trace_attribution.py"),
    Path("tools/build_post_rebuild_near_tie_stability_policy_design.py"),
    Path("tools/build_post_rebuild_near_tie_patch_validation.py"),
    Path("tools/build_post_rebuild_near_tie_patch_closeout.py"),
    Path("tools/build_base_candidate_mismatch_summary.py"),
]

FORBIDDEN_IMPORT_KEYS = {
    "reviewer",
    "reviewed_at",
    "decision",
    "confirmed_root_causes",
    "rejected_root_causes",
    "confirmed_follow_up_actions",
    "proposed_change_targets",
    "fixture_candidate",
    "rationale",
    "notes",
    "reviewer_decision",
    "reviewer_input_template",
    "workbench_items",
    "decision_status",
}

PROHIBITED_OFFLINE_PATTERNS = [
    "fetch(",
    "XMLHttpRequest",
    "/ask",
    "rag_query(",
    "from src.rag.retriever import rag_query",
    "ChatOpenAI",
    "QdrantClient",
]

ENCODING_HYGIENE_REPORT_PATH = Path("tests/encoding_hygiene_report.json")
TOOL_INDEX_CONSISTENCY_REPORT_PATH = Path("tests/tool_index_consistency_report.json")
TEST_INDEX_CONSISTENCY_REPORT_PATH = Path("tests/test_index_consistency_report.json")
ARTIFACT_INDEX_CONSISTENCY_REPORT_PATH = Path("tests/artifact_index_consistency_report.json")
LAYOUT_MIGRATION_READINESS_REPORT_PATH = Path("tests/layout_migration_readiness_report.json")
MAINTENANCE_CLOSEOUT_REPORT_PATH = Path("tests/maintenance_closeout_report.json")

LAYOUT_COMPATIBILITY_REPORTS = [
    ("tests/rag_eval_report.json", "eval"),
    ("tests/risk_eval_report.json", "eval"),
    ("tests/manual_review_prescreen_report.json", "manual_review"),
    ("tests/manual_review_visual_workbench_build_report.json", "manual_review"),
    ("tests/manual_review_workbench_import_report.json", "manual_review"),
    ("tests/pilot_manual_review_round1_support_report.json", "manual_review"),
    ("tests/mobile_pilot_review_decision_aid_report.json", "manual_review"),
    ("tests/manual_review_export_pipeline_dry_run_report.json", "dry_run"),
    ("tests/ready_action_design_pack_report.json", "dry_run"),
    ("tests/ready_action_design_review_brief_report.json", "dry_run"),
    ("tests/ready_action_design_review_gate_report.json", "dry_run"),
    ("tests/ready_action_design_review_worksheet_report.json", "dry_run"),
    ("tests/ready_action_design_review_closeout_report.json", "dry_run"),
    ("tests/ready_action_human_closeout_decision_draft_report.json", "dry_run"),
    ("tests/ready_action_human_closeout_confirmation_record_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_intake_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_simulator_spec_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_table_draft_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_human_review_worksheet_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_closeout_envelope_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_closeout_decision_draft_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_closeout_confirmation_record_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_closeout_confirmed_record_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_language_revision_worksheet_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_offline_simulation_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_offline_simulation_gate_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_adoption_decision_draft_report.json", "dry_run"),
    ("tests/final_evidence_selection_policy_series_closeout_report.json", "dry_run"),
    ("tests/retrieval_input_quality_intake_report.json", "dry_run"),
    ("tests/retrieval_input_quality_audit_spec_report.json", "dry_run"),
    ("tests/retrieval_input_quality_offline_audit_report.json", "dry_run"),
    ("tests/retrieval_input_quality_offline_audit_gate_report.json", "dry_run"),
    ("tests/retrieval_input_quality_diagnostic_prioritization_report.json", "dry_run"),
    ("tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json", "dry_run"),
    ("tests/metadata_chunking_diagnostic_spec_report.json", "dry_run"),
    ("tests/metadata_chunking_diagnostic_spec_gate_report.json", "dry_run"),
    ("tests/metadata_chunking_diagnostic_runner_design_report.json", "dry_run"),
    ("tests/metadata_chunking_diagnostic_runner_design_gate_report.json", "dry_run"),
    ("tests/metadata_chunking_diagnostic_dry_run_contract_report.json", "dry_run"),
    ("tests/retrieval_input_quality_series_closeout_report.json", "dry_run"),
    ("tests/metadata_chunking_diagnostic_runner_manifest_report.json", "dry_run"),
    ("tests/metadata_chunking_diagnostic_saved_report_runner_report.json", "dry_run"),
    ("tests/metadata_chunking_diagnostic_saved_report_runner_gate_report.json", "dry_run"),
    ("tests/metadata_chunking_diagnostic_runner_series_closeout_report.json", "dry_run"),
    ("tests/evidence_metadata_snapshot_contract_report.json", "dry_run"),
    ("tests/evidence_metadata_snapshot_report.json", "dry_run"),
    ("tests/evidence_metadata_snapshot_gate_report.json", "dry_run"),
    ("tests/evidence_metadata_snapshot_series_closeout_report.json", "dry_run"),
    ("tests/metadata_chunking_root_cause_report.json", "dry_run"),
    ("tests/metadata_chunking_fix_design_report.json", "dry_run"),
    ("tests/metadata_chunking_fix_design_gate_report.json", "dry_run"),
    ("tests/metadata_chunking_series_closeout_report.json", "dry_run"),
    ("tests/ingestion_metadata_patch_contract_report.json", "dry_run"),
    ("tests/ingestion_metadata_patch_contract_gate_report.json", "dry_run"),
    ("tests/ingestion_metadata_patch_dry_run_design_report.json", "dry_run"),
    ("tests/ingestion_metadata_patch_dry_run_design_gate_report.json", "dry_run"),
    ("tests/ingestion_metadata_patch_local_dry_run_report.json", "dry_run"),
    ("tests/ingestion_metadata_patch_local_dry_run_gate_report.json", "dry_run"),
    ("tests/ingestion_metadata_patch_actual_design_report.json", "dry_run"),
    ("tests/ingestion_metadata_patch_actual_design_gate_report.json", "dry_run"),
    ("tests/ingestion_metadata_source_patch_report.json", "dry_run"),
    ("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json", "dry_run"),
    ("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json", "dry_run"),
    ("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json", "dry_run"),
    ("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json", "dry_run"),
    ("tests/rebuild_authorization_design_report.json", "dry_run"),
    ("tests/rebuild_authorization_design_gate_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_worksheet_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_worksheet_gate_report.json", "dry_run"),
    ("tests/rebuild_runbook_preflight_contract_report.json", "dry_run"),
    ("tests/ingestion_metadata_rebuild_planning_series_closeout_report.json", "dry_run"),
    ("tests/production_rebuild_execution_design_report.json", "dry_run"),
    ("tests/production_rebuild_execution_design_gate_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_record_scaffold_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_record_scaffold_gate_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_record_draft_design_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_record_draft_design_gate_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_record_draft_scaffold_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_record_draft_scaffold_gate_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_record_input_workflow_design_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_record_input_workflow_design_gate_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_record_input_packet_scaffold_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_record_input_packet_scaffold_gate_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_record_input_form_scaffold_report.json", "dry_run"),
    ("tests/human_rebuild_authorization_record_input_form_scaffold_gate_report.json", "dry_run"),
    ("tests/production_rebuild_readiness_cutoff_report.json", "dry_run"),
    ("tests/production_rebuild_live_preflight_runner_design_report.json", "dry_run"),
    ("tests/production_rebuild_live_preflight_runner_design_gate_report.json", "dry_run"),
    ("tests/production_rebuild_live_preflight_runner_minimal_implementation_design_report.json", "dry_run"),
    ("tests/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json", "dry_run"),
    ("tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json", "dry_run"),
    ("tests/base_retrieval_quality_audit_report.json", "audits"),
]

LAYOUT_HELPER_PILOT_DEFAULTS = {
    "tools/check_evidence_alignment.py": {
        "DEFAULT_RAG_REPORT_PATH": Path("tests/rag_eval_report.json"),
        "DEFAULT_HIDDEN_REPORT_PATH": Path("tests/hidden_eval_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/evidence_alignment_report.json"),
    },
    "tools/check_evidence_coverage.py": {
        "DEFAULT_RAG_REPORT_PATH": Path("tests/rag_eval_report.json"),
        "DEFAULT_HIDDEN_REPORT_PATH": Path("tests/hidden_eval_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/evidence_coverage_report.json"),
    },
    "tools/check_legal_functional_type_config.py": {
        "DEFAULT_REPORT_PATH": Path("tests/legal_functional_type_config_report.json"),
    },
    "tools/build_evidence_manual_review_dataset.py": {
        "DEFAULT_COVERAGE_REPORT_PATH": Path("tests/evidence_coverage_report.json"),
        "DEFAULT_TRIAGE_REPORT_PATH": Path("tests/evidence_coverage_triage_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/evidence_manual_review_dataset.json"),
    },
    "tools/build_evidence_root_cause_action_plan.py": {
        "DEFAULT_COVERAGE_REPORT_PATH": Path("tests/evidence_coverage_report.json"),
        "DEFAULT_TRIAGE_REPORT_PATH": Path("tests/evidence_coverage_triage_report.json"),
        "DEFAULT_MANUAL_REVIEW_DATASET_PATH": Path("tests/evidence_manual_review_dataset.json"),
        "DEFAULT_GATE_DRAFT_REPORT_PATH": Path("tests/evidence_coverage_gate_draft_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/evidence_root_cause_action_plan.json"),
    },
    "tools/build_evidence_action_series_baseline.py": {
        "DEFAULT_ACTION_PLAN_PATH": Path("tests/evidence_root_cause_action_plan.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/evidence_action_series_baseline.json"),
    },
    "tools/draft_evidence_coverage_gates.py": {
        "DEFAULT_COVERAGE_REPORT_PATH": Path("tests/evidence_coverage_report.json"),
        "DEFAULT_TRIAGE_REPORT_PATH": Path("tests/evidence_coverage_triage_report.json"),
        "DEFAULT_MANUAL_REVIEW_DATASET_PATH": Path("tests/evidence_manual_review_dataset.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/evidence_coverage_gate_draft_report.json"),
    },
    "tools/build_manual_review_visual_workbench.py": {
        "DEFAULT_CONTRACT_REPORT_PATH": Path("tests/manual_review_visual_workbench_contract_report.json"),
        "DEFAULT_INTAKE_CONTRACT_PATH": Path("tests/manual_review_intake_contract_report.json"),
        "DEFAULT_PROGRESS_REPORT_PATH": Path("tests/evidence_manual_review_progress_report.json"),
        "DEFAULT_GOVERNANCE_REPORT_PATH": Path("tests/evidence_manual_review_governance_report.json"),
        "DEFAULT_IMPORT_REPORT_PATH": Path("tests/manual_review_workbench_import_report.json"),
        "DEFAULT_DIFF_REPORT_PATH": Path("tests/manual_review_decision_diff_report.json"),
        "DEFAULT_VALIDATION_REPORT_PATH": Path("tests/proposed_manual_review_decision_validation_report.json"),
        "DEFAULT_PROMOTION_REPORT_PATH": Path("tests/validated_decision_promotion_dry_run_report.json"),
        "DEFAULT_CLOSEOUT_REPORT_PATH": Path("tests/manual_review_intake_gate_closeout_report.json"),
        "DEFAULT_PILOT_BATCH_REPORT_PATH": Path("tests/manual_review_pilot_batch_report.json"),
        "DEFAULT_PILOT_REVIEW_ASSIST_REPORT_PATH": Path("tests/manual_review_pilot_case_review_assist_report.json"),
        "DEFAULT_REPORT_OUTPUT_PATH": Path("tests/manual_review_visual_workbench_build_report.json"),
    },
    "tools/import_manual_review_workbench.py": {
        "DEFAULT_REPORT_PATH": Path("tests/manual_review_workbench_import_report.json"),
    },
    "tools/build_manual_review_export_pipeline_dry_run.py": {
        "DEFAULT_CONTRACT_REPORT_PATH": Path("tests/manual_review_intake_contract_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/manual_review_export_pipeline_dry_run_report.json"),
    },
    "tools/build_pilot_manual_review_round1_support.py": {
        "DEFAULT_PILOT_BATCH_PATH": Path("tests/manual_review_pilot_batch_report.json"),
        "DEFAULT_PILOT_REVIEW_ASSIST_PATH": Path("tests/manual_review_pilot_case_review_assist_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/pilot_manual_review_round1_support_report.json"),
    },
    "tools/build_mobile_pilot_review_decision_aid.py": {
        "DEFAULT_ROUND1_SUPPORT_PATH": Path("tests/pilot_manual_review_round1_support_report.json"),
        "DEFAULT_CONTRACT_PATH": Path("tests/manual_review_visual_workbench_contract_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/mobile_pilot_review_decision_aid_report.json"),
    },
    "tools/build_ready_action_design_pack.py": {
        "DEFAULT_PROMOTION_REPORT_PATH": Path("tests/validated_decision_promotion_dry_run_report.json"),
        "DEFAULT_EXPORT_PIPELINE_DRY_RUN_REPORT_PATH": Path("tests/manual_review_export_pipeline_dry_run_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ready_action_design_pack_report.json"),
    },
    "tools/build_ready_action_design_review_brief.py": {
        "DEFAULT_DESIGN_PACK_REPORT_PATH": Path("tests/ready_action_design_pack_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ready_action_design_review_brief_report.json"),
    },
    "tools/check_ready_action_design_review_gate.py": {
        "DEFAULT_BRIEF_REPORT_PATH": Path("tests/ready_action_design_review_brief_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ready_action_design_review_gate_report.json"),
    },
    "tools/build_ready_action_design_review_worksheet.py": {
        "DEFAULT_GATE_REPORT_PATH": Path("tests/ready_action_design_review_gate_report.json"),
        "DEFAULT_BRIEF_REPORT_PATH": Path("tests/ready_action_design_review_brief_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ready_action_design_review_worksheet_report.json"),
    },
    "tools/build_ready_action_design_review_closeout.py": {
        "DEFAULT_WORKSHEET_REPORT_PATH": Path("tests/ready_action_design_review_worksheet_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ready_action_design_review_closeout_report.json"),
    },
    "tools/build_ready_action_human_closeout_decision_draft.py": {
        "DEFAULT_CLOSEOUT_REPORT_PATH": Path("tests/ready_action_design_review_closeout_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ready_action_human_closeout_decision_draft_report.json"),
    },
    "tools/build_ready_action_human_closeout_confirmation_record.py": {
        "DEFAULT_DRAFT_REPORT_PATH": Path("tests/ready_action_human_closeout_decision_draft_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ready_action_human_closeout_confirmation_record_report.json"),
    },
    "tools/build_final_evidence_selection_policy_intake.py": {
        "DEFAULT_CONFIRMATION_REPORT_PATH": Path("tests/ready_action_human_closeout_confirmation_record_report.json"),
        "DEFAULT_DECISION_DRAFT_REPORT_PATH": Path("tests/ready_action_human_closeout_decision_draft_report.json"),
        "DEFAULT_CLOSEOUT_REPORT_PATH": Path("tests/ready_action_design_review_closeout_report.json"),
        "DEFAULT_WORKSHEET_REPORT_PATH": Path("tests/ready_action_design_review_worksheet_report.json"),
        "DEFAULT_DESIGN_PACK_REPORT_PATH": Path("tests/ready_action_design_pack_report.json"),
        "DEFAULT_FINAL_SELECTION_AUDIT_REPORT_PATH": Path("tests/final_evidence_selection_audit_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_intake_report.json"),
    },
    "tools/build_final_evidence_selection_policy_simulator_spec.py": {
        "DEFAULT_INTAKE_REPORT_PATH": Path("tests/final_evidence_selection_policy_intake_report.json"),
        "DEFAULT_AUDIT_REPORT_PATH": Path("tests/final_evidence_selection_audit_report.json"),
        "DEFAULT_CONFIRMATION_REPORT_PATH": Path("tests/ready_action_human_closeout_confirmation_record_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_simulator_spec_report.json"),
    },
    "tools/build_final_evidence_selection_policy_table_draft.py": {
        "DEFAULT_SIMULATOR_SPEC_REPORT_PATH": Path("tests/final_evidence_selection_policy_simulator_spec_report.json"),
        "DEFAULT_INTAKE_REPORT_PATH": Path("tests/final_evidence_selection_policy_intake_report.json"),
        "DEFAULT_AUDIT_REPORT_PATH": Path("tests/final_evidence_selection_audit_report.json"),
        "DEFAULT_CONFIRMATION_REPORT_PATH": Path("tests/ready_action_human_closeout_confirmation_record_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_table_draft_report.json"),
    },
    "tools/build_final_evidence_selection_policy_human_review_worksheet.py": {
        "DEFAULT_TABLE_DRAFT_REPORT_PATH": Path("tests/final_evidence_selection_policy_table_draft_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_human_review_worksheet_report.json"),
    },
    "tools/build_final_evidence_selection_policy_closeout_envelope.py": {
        "DEFAULT_WORKSHEET_REPORT_PATH": Path("tests/final_evidence_selection_policy_human_review_worksheet_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_closeout_envelope_report.json"),
    },
    "tools/build_final_evidence_selection_policy_closeout_decision_draft.py": {
        "DEFAULT_CLOSEOUT_REPORT_PATH": Path("tests/final_evidence_selection_policy_closeout_envelope_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_closeout_decision_draft_report.json"),
    },
    "tools/build_final_evidence_selection_policy_closeout_confirmation_record.py": {
        "DEFAULT_DRAFT_REPORT_PATH": Path("tests/final_evidence_selection_policy_closeout_decision_draft_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_closeout_confirmation_record_report.json"),
    },
    "tools/build_final_evidence_selection_policy_closeout_confirmed_record.py": {
        "DEFAULT_SCAFFOLD_REPORT_PATH": Path("tests/final_evidence_selection_policy_closeout_confirmation_record_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_closeout_confirmed_record_report.json"),
    },
    "tools/build_final_evidence_selection_policy_language_revision_worksheet.py": {
        "DEFAULT_CONFIRMED_RECORD_PATH": Path("tests/final_evidence_selection_policy_closeout_confirmed_record_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_language_revision_worksheet_report.json"),
    },
    "tools/build_final_evidence_selection_policy_language_revision_closeout_draft.py": {
        "DEFAULT_WORKSHEET_PATH": Path("tests/final_evidence_selection_policy_language_revision_worksheet_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json"),
    },
    "tools/build_final_evidence_selection_policy_language_revision_confirmation_record.py": {
        "DEFAULT_DRAFT_PATH": Path("tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json"),
    },
    "tools/build_final_evidence_selection_policy_offline_simulation_input_contract.py": {
        "DEFAULT_CONFIRMED_RECORD_PATH": Path("tests/final_evidence_selection_policy_closeout_confirmed_record_report.json"),
        "DEFAULT_LANGUAGE_CONFIRMATION_PATH": Path("tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json"),
    },
    "tools/build_final_evidence_selection_policy_offline_simulation.py": {
        "DEFAULT_INPUT_CONTRACT_PATH": Path("tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_offline_simulation_report.json"),
    },
    "tools/check_final_evidence_selection_policy_offline_simulation_gate.py": {
        "DEFAULT_SIMULATION_REPORT_PATH": Path("tests/final_evidence_selection_policy_offline_simulation_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_offline_simulation_gate_report.json"),
    },
    "tools/build_final_evidence_selection_policy_adoption_decision_draft.py": {
        "DEFAULT_GATE_REPORT_PATH": Path("tests/final_evidence_selection_policy_offline_simulation_gate_report.json"),
        "DEFAULT_SIMULATION_REPORT_PATH": Path("tests/final_evidence_selection_policy_offline_simulation_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_adoption_decision_draft_report.json"),
    },
    "tools/build_final_evidence_selection_policy_series_closeout.py": {
        "DEFAULT_ADOPTION_DRAFT_PATH": Path("tests/final_evidence_selection_policy_adoption_decision_draft_report.json"),
        "DEFAULT_GATE_REPORT_PATH": Path("tests/final_evidence_selection_policy_offline_simulation_gate_report.json"),
        "DEFAULT_SIMULATION_REPORT_PATH": Path("tests/final_evidence_selection_policy_offline_simulation_report.json"),
        "DEFAULT_INPUT_CONTRACT_PATH": Path("tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/final_evidence_selection_policy_series_closeout_report.json"),
    },
    "tools/build_retrieval_input_quality_intake.py": {
        "DEFAULT_BASE_RETRIEVAL_AUDIT_PATH": Path("tests/base_retrieval_quality_audit_report.json"),
        "DEFAULT_ANCHOR_DEPENDENCY_AUDIT_PATH": Path("tests/anchor_dependency_audit_report.json"),
        "DEFAULT_ROOT_CAUSE_ACTION_PLAN_PATH": Path("tests/evidence_root_cause_action_plan.json"),
        "DEFAULT_SERIES_CLOSEOUT_PATH": Path("tests/final_evidence_selection_policy_series_closeout_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/retrieval_input_quality_intake_report.json"),
    },
    "tools/build_retrieval_input_quality_audit_spec.py": {
        "DEFAULT_INTAKE_REPORT_PATH": Path("tests/retrieval_input_quality_intake_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/retrieval_input_quality_audit_spec_report.json"),
    },
    "tools/build_retrieval_input_quality_offline_audit.py": {
        "DEFAULT_AUDIT_SPEC_PATH": Path("tests/retrieval_input_quality_audit_spec_report.json"),
        "DEFAULT_INTAKE_REPORT_PATH": Path("tests/retrieval_input_quality_intake_report.json"),
        "DEFAULT_BASE_RETRIEVAL_AUDIT_PATH": Path("tests/base_retrieval_quality_audit_report.json"),
        "DEFAULT_ANCHOR_DEPENDENCY_AUDIT_PATH": Path("tests/anchor_dependency_audit_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/retrieval_input_quality_offline_audit_report.json"),
    },
    "tools/check_retrieval_input_quality_offline_audit_gate.py": {
        "DEFAULT_OFFLINE_AUDIT_REPORT_PATH": Path("tests/retrieval_input_quality_offline_audit_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/retrieval_input_quality_offline_audit_gate_report.json"),
    },
    "tools/build_retrieval_input_quality_diagnostic_prioritization.py": {
        "DEFAULT_GATE_REPORT_PATH": Path("tests/retrieval_input_quality_offline_audit_gate_report.json"),
        "DEFAULT_OFFLINE_AUDIT_REPORT_PATH": Path("tests/retrieval_input_quality_offline_audit_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/retrieval_input_quality_diagnostic_prioritization_report.json"),
    },
    "tools/check_retrieval_input_quality_diagnostic_prioritization_gate.py": {
        "DEFAULT_PRIORITIZATION_REPORT_PATH": Path("tests/retrieval_input_quality_diagnostic_prioritization_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json"),
    },
    "tools/build_metadata_chunking_diagnostic_spec.py": {
        "DEFAULT_PRIORITIZATION_GATE_REPORT_PATH": Path("tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json"),
        "DEFAULT_PRIORITIZATION_REPORT_PATH": Path("tests/retrieval_input_quality_diagnostic_prioritization_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/metadata_chunking_diagnostic_spec_report.json"),
    },
    "tools/check_metadata_chunking_diagnostic_spec_gate.py": {
        "DEFAULT_SPEC_REPORT_PATH": Path("tests/metadata_chunking_diagnostic_spec_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/metadata_chunking_diagnostic_spec_gate_report.json"),
    },
    "tools/build_metadata_chunking_diagnostic_runner_design.py": {
        "DEFAULT_SPEC_GATE_REPORT_PATH": Path("tests/metadata_chunking_diagnostic_spec_gate_report.json"),
        "DEFAULT_SPEC_REPORT_PATH": Path("tests/metadata_chunking_diagnostic_spec_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/metadata_chunking_diagnostic_runner_design_report.json"),
    },
    "tools/check_metadata_chunking_diagnostic_runner_design_gate.py": {
        "DEFAULT_RUNNER_DESIGN_REPORT_PATH": Path("tests/metadata_chunking_diagnostic_runner_design_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/metadata_chunking_diagnostic_runner_design_gate_report.json"),
    },
    "tools/build_metadata_chunking_diagnostic_dry_run_contract.py": {
        "DEFAULT_RUNNER_DESIGN_GATE_REPORT_PATH": Path("tests/metadata_chunking_diagnostic_runner_design_gate_report.json"),
        "DEFAULT_RUNNER_DESIGN_REPORT_PATH": Path("tests/metadata_chunking_diagnostic_runner_design_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/metadata_chunking_diagnostic_dry_run_contract_report.json"),
    },
    "tools/build_retrieval_input_quality_series_closeout.py": {
        "DEFAULT_OUTPUT_PATH": Path("tests/retrieval_input_quality_series_closeout_report.json"),
    },
    "tools/build_metadata_chunking_diagnostic_runner_manifest.py": {
        "DEFAULT_SERIES_CLOSEOUT_REPORT_PATH": Path("tests/retrieval_input_quality_series_closeout_report.json"),
        "DEFAULT_DRY_RUN_CONTRACT_REPORT_PATH": Path("tests/metadata_chunking_diagnostic_dry_run_contract_report.json"),
        "DEFAULT_SPEC_REPORT_PATH": Path("tests/metadata_chunking_diagnostic_spec_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/metadata_chunking_diagnostic_runner_manifest_report.json"),
    },
    "tools/run_metadata_chunking_diagnostic_saved_report.py": {
        "DEFAULT_MANIFEST_REPORT_PATH": Path("tests/metadata_chunking_diagnostic_runner_manifest_report.json"),
        "DEFAULT_DRY_RUN_CONTRACT_REPORT_PATH": Path("tests/metadata_chunking_diagnostic_dry_run_contract_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/metadata_chunking_diagnostic_saved_report_runner_report.json"),
    },
    "tools/check_metadata_chunking_diagnostic_saved_report_runner_gate.py": {
        "DEFAULT_RUNNER_REPORT_PATH": Path("tests/metadata_chunking_diagnostic_saved_report_runner_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/metadata_chunking_diagnostic_saved_report_runner_gate_report.json"),
    },
    "tools/build_metadata_chunking_diagnostic_runner_series_closeout.py": {
        "DEFAULT_MANIFEST_PATH": Path("tests/metadata_chunking_diagnostic_runner_manifest_report.json"),
        "DEFAULT_RUNNER_PATH": Path("tests/metadata_chunking_diagnostic_saved_report_runner_report.json"),
        "DEFAULT_GATE_PATH": Path("tests/metadata_chunking_diagnostic_saved_report_runner_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/metadata_chunking_diagnostic_runner_series_closeout_report.json"),
    },
    "tools/build_evidence_metadata_snapshot_contract.py": {
        "DEFAULT_CLOSEOUT_PATH": Path("tests/metadata_chunking_diagnostic_runner_series_closeout_report.json"),
        "DEFAULT_MANIFEST_PATH": Path("tests/metadata_chunking_diagnostic_runner_manifest_report.json"),
        "DEFAULT_EVAL_CASES_PATH": Path("tests/rag_eval_cases.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/evidence_metadata_snapshot_contract_report.json"),
    },
    "tools/run_evidence_metadata_snapshot.py": {
        "DEFAULT_CONTRACT_PATH": Path("tests/evidence_metadata_snapshot_contract_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/evidence_metadata_snapshot_report.json"),
    },
    "tools/check_evidence_metadata_snapshot_gate.py": {
        "DEFAULT_SNAPSHOT_PATH": Path("tests/evidence_metadata_snapshot_report.json"),
        "DEFAULT_CONTRACT_PATH": Path("tests/evidence_metadata_snapshot_contract_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/evidence_metadata_snapshot_gate_report.json"),
    },
    "tools/build_evidence_metadata_snapshot_series_closeout.py": {
        "DEFAULT_CONTRACT_PATH": Path("tests/evidence_metadata_snapshot_contract_report.json"),
        "DEFAULT_SNAPSHOT_PATH": Path("tests/evidence_metadata_snapshot_report.json"),
        "DEFAULT_GATE_PATH": Path("tests/evidence_metadata_snapshot_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/evidence_metadata_snapshot_series_closeout_report.json"),
    },
    "tools/build_metadata_chunking_root_cause_report.py": {
        "DEFAULT_CLOSEOUT_PATH": Path("tests/evidence_metadata_snapshot_series_closeout_report.json"),
        "DEFAULT_SNAPSHOT_PATH": Path("tests/evidence_metadata_snapshot_report.json"),
        "DEFAULT_QDRANT_INTEGRITY_PATH": Path("tests/qdrant_index_integrity_report.json"),
        "DEFAULT_INGESTION_PATH": Path("src/rag/ingestion.py"),
        "DEFAULT_OUTPUT_PATH": Path("tests/metadata_chunking_root_cause_report.json"),
    },
    "tools/build_metadata_chunking_fix_design.py": {
        "DEFAULT_ROOT_CAUSE_PATH": Path("tests/metadata_chunking_root_cause_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/metadata_chunking_fix_design_report.json"),
    },
    "tools/check_metadata_chunking_fix_design_gate.py": {
        "DEFAULT_FIX_DESIGN_PATH": Path("tests/metadata_chunking_fix_design_report.json"),
        "DEFAULT_ROOT_CAUSE_PATH": Path("tests/metadata_chunking_root_cause_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/metadata_chunking_fix_design_gate_report.json"),
    },
    "tools/build_metadata_chunking_series_closeout.py": {
        "DEFAULT_ROOT_CAUSE_PATH": Path("tests/metadata_chunking_root_cause_report.json"),
        "DEFAULT_FIX_DESIGN_PATH": Path("tests/metadata_chunking_fix_design_report.json"),
        "DEFAULT_FIX_DESIGN_GATE_PATH": Path("tests/metadata_chunking_fix_design_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/metadata_chunking_series_closeout_report.json"),
    },
    "tools/build_ingestion_metadata_patch_contract.py": {
        "DEFAULT_SERIES_CLOSEOUT_PATH": Path("tests/metadata_chunking_series_closeout_report.json"),
        "DEFAULT_FIX_DESIGN_PATH": Path("tests/metadata_chunking_fix_design_report.json"),
        "DEFAULT_INGESTION_PATH": Path("src/rag/ingestion.py"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_patch_contract_report.json"),
    },
    "tools/check_ingestion_metadata_patch_contract_gate.py": {
        "DEFAULT_CONTRACT_PATH": Path("tests/ingestion_metadata_patch_contract_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_patch_contract_gate_report.json"),
    },
    "tools/build_ingestion_metadata_patch_dry_run_design.py": {
        "DEFAULT_CONTRACT_PATH": Path("tests/ingestion_metadata_patch_contract_report.json"),
        "DEFAULT_CONTRACT_GATE_PATH": Path("tests/ingestion_metadata_patch_contract_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_patch_dry_run_design_report.json"),
    },
    "tools/check_ingestion_metadata_patch_dry_run_design_gate.py": {
        "DEFAULT_DRY_RUN_DESIGN_PATH": Path("tests/ingestion_metadata_patch_dry_run_design_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_patch_dry_run_design_gate_report.json"),
    },
    "tools/run_ingestion_metadata_patch_local_dry_run.py": {
        "DEFAULT_DRY_RUN_DESIGN_PATH": Path("tests/ingestion_metadata_patch_dry_run_design_report.json"),
        "DEFAULT_DRY_RUN_DESIGN_GATE_PATH": Path("tests/ingestion_metadata_patch_dry_run_design_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_patch_local_dry_run_report.json"),
    },
    "tools/check_ingestion_metadata_patch_local_dry_run_gate.py": {
        "DEFAULT_LOCAL_DRY_RUN_PATH": Path("tests/ingestion_metadata_patch_local_dry_run_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_patch_local_dry_run_gate_report.json"),
    },
    "tools/build_ingestion_metadata_patch_actual_design.py": {
        "DEFAULT_CONTRACT_PATH": Path("tests/ingestion_metadata_patch_contract_report.json"),
        "DEFAULT_LOCAL_DRY_RUN_PATH": Path("tests/ingestion_metadata_patch_local_dry_run_report.json"),
        "DEFAULT_LOCAL_DRY_RUN_GATE_PATH": Path("tests/ingestion_metadata_patch_local_dry_run_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_patch_actual_design_report.json"),
    },
    "tools/check_ingestion_metadata_patch_actual_design_gate.py": {
        "DEFAULT_ACTUAL_DESIGN_PATH": Path("tests/ingestion_metadata_patch_actual_design_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_patch_actual_design_gate_report.json"),
    },
    "tools/check_ingestion_metadata_source_patch.py": {
        "DEFAULT_GATE_PATH": Path("tests/ingestion_metadata_patch_actual_design_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_source_patch_report.json"),
    },
    "tools/build_ingestion_metadata_patch_post_patch_rebuild_dry_run_design.py": {
        "DEFAULT_SOURCE_PATCH_REPORT_PATH": Path("tests/ingestion_metadata_source_patch_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json"),
    },
    "tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate.py": {
        "DEFAULT_DESIGN_PATH": Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json"),
    },
    "tools/run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py": {
        "DEFAULT_SOURCE_PATCH_REPORT_PATH": Path("tests/ingestion_metadata_source_patch_report.json"),
        "DEFAULT_DESIGN_PATH": Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json"),
        "DEFAULT_DESIGN_GATE_PATH": Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json"),
    },
    "tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate.py": {
        "DEFAULT_RUNNER_REPORT_PATH": Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json"),
    },
    "tools/build_rebuild_authorization_design.py": {
        "DEFAULT_RUNNER_REPORT_PATH": Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json"),
        "DEFAULT_RUNNER_GATE_REPORT_PATH": Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/rebuild_authorization_design_report.json"),
    },
    "tools/check_rebuild_authorization_design_gate.py": {
        "DEFAULT_DESIGN_PATH": Path("tests/rebuild_authorization_design_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/rebuild_authorization_design_gate_report.json"),
    },
    "tools/build_human_rebuild_authorization_worksheet.py": {
        "DEFAULT_DESIGN_PATH": Path("tests/rebuild_authorization_design_report.json"),
        "DEFAULT_DESIGN_GATE_PATH": Path("tests/rebuild_authorization_design_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_worksheet_report.json"),
    },
    "tools/check_human_rebuild_authorization_worksheet_gate.py": {
        "DEFAULT_WORKSHEET_PATH": Path("tests/human_rebuild_authorization_worksheet_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_worksheet_gate_report.json"),
    },
    "tools/build_rebuild_runbook_preflight_contract.py": {
        "DEFAULT_WORKSHEET_GATE_PATH": Path("tests/human_rebuild_authorization_worksheet_gate_report.json"),
        "DEFAULT_WORKSHEET_PATH": Path("tests/human_rebuild_authorization_worksheet_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/rebuild_runbook_preflight_contract_report.json"),
    },
    "tools/build_ingestion_metadata_rebuild_planning_series_closeout.py": {
        "DEFAULT_AUTH_DESIGN_PATH": Path("tests/rebuild_authorization_design_report.json"),
        "DEFAULT_AUTH_GATE_PATH": Path("tests/rebuild_authorization_design_gate_report.json"),
        "DEFAULT_WORKSHEET_PATH": Path("tests/human_rebuild_authorization_worksheet_report.json"),
        "DEFAULT_WORKSHEET_GATE_PATH": Path("tests/human_rebuild_authorization_worksheet_gate_report.json"),
        "DEFAULT_RUNBOOK_PATH": Path("tests/rebuild_runbook_preflight_contract_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/ingestion_metadata_rebuild_planning_series_closeout_report.json"),
    },
    "tools/build_production_rebuild_execution_design.py": {
        "DEFAULT_CLOSEOUT_PATH": Path("tests/ingestion_metadata_rebuild_planning_series_closeout_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/production_rebuild_execution_design_report.json"),
    },
    "tools/check_production_rebuild_execution_design_gate.py": {
        "DEFAULT_DESIGN_PATH": Path("tests/production_rebuild_execution_design_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/production_rebuild_execution_design_gate_report.json"),
    },
    "tools/build_human_rebuild_authorization_record_scaffold.py": {
        "DEFAULT_DESIGN_PATH": Path("tests/production_rebuild_execution_design_report.json"),
        "DEFAULT_DESIGN_GATE_PATH": Path("tests/production_rebuild_execution_design_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_record_scaffold_report.json"),
    },
    "tools/check_human_rebuild_authorization_record_scaffold_gate.py": {
        "DEFAULT_SCAFFOLD_PATH": Path("tests/human_rebuild_authorization_record_scaffold_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_record_scaffold_gate_report.json"),
    },
    "tools/build_human_rebuild_authorization_record_draft_design.py": {
        "DEFAULT_SCAFFOLD_PATH": Path("tests/human_rebuild_authorization_record_scaffold_report.json"),
        "DEFAULT_SCAFFOLD_GATE_PATH": Path("tests/human_rebuild_authorization_record_scaffold_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_record_draft_design_report.json"),
    },
    "tools/check_human_rebuild_authorization_record_draft_design_gate.py": {
        "DEFAULT_DRAFT_DESIGN_PATH": Path("tests/human_rebuild_authorization_record_draft_design_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_record_draft_design_gate_report.json"),
    },
    "tools/build_human_rebuild_authorization_record_draft_scaffold.py": {
        "DEFAULT_DRAFT_DESIGN_PATH": Path("tests/human_rebuild_authorization_record_draft_design_report.json"),
        "DEFAULT_DRAFT_DESIGN_GATE_PATH": Path("tests/human_rebuild_authorization_record_draft_design_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_record_draft_scaffold_report.json"),
    },
    "tools/check_human_rebuild_authorization_record_draft_scaffold_gate.py": {
        "DEFAULT_DRAFT_SCAFFOLD_PATH": Path("tests/human_rebuild_authorization_record_draft_scaffold_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_record_draft_scaffold_gate_report.json"),
    },
    "tools/build_human_rebuild_authorization_record_input_workflow_design.py": {
        "DEFAULT_DRAFT_SCAFFOLD_PATH": Path("tests/human_rebuild_authorization_record_draft_scaffold_report.json"),
        "DEFAULT_DRAFT_SCAFFOLD_GATE_PATH": Path("tests/human_rebuild_authorization_record_draft_scaffold_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_record_input_workflow_design_report.json"),
    },
    "tools/check_human_rebuild_authorization_record_input_workflow_design_gate.py": {
        "DEFAULT_INPUT_WORKFLOW_DESIGN_PATH": Path(
            "tests/human_rebuild_authorization_record_input_workflow_design_report.json"
        ),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_record_input_workflow_design_gate_report.json"),
    },
    "tools/build_human_rebuild_authorization_record_input_packet_scaffold.py": {
        "DEFAULT_INPUT_WORKFLOW_DESIGN_PATH": Path(
            "tests/human_rebuild_authorization_record_input_workflow_design_report.json"
        ),
        "DEFAULT_INPUT_WORKFLOW_DESIGN_GATE_PATH": Path(
            "tests/human_rebuild_authorization_record_input_workflow_design_gate_report.json"
        ),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_record_input_packet_scaffold_report.json"),
    },
    "tools/check_human_rebuild_authorization_record_input_packet_scaffold_gate.py": {
        "DEFAULT_INPUT_PACKET_SCAFFOLD_PATH": Path(
            "tests/human_rebuild_authorization_record_input_packet_scaffold_report.json"
        ),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_record_input_packet_scaffold_gate_report.json"),
    },
    "tools/build_human_rebuild_authorization_record_input_form_scaffold.py": {
        "DEFAULT_INPUT_PACKET_SCAFFOLD_PATH": Path(
            "tests/human_rebuild_authorization_record_input_packet_scaffold_report.json"
        ),
        "DEFAULT_INPUT_PACKET_SCAFFOLD_GATE_PATH": Path(
            "tests/human_rebuild_authorization_record_input_packet_scaffold_gate_report.json"
        ),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_record_input_form_scaffold_report.json"),
    },
    "tools/check_human_rebuild_authorization_record_input_form_scaffold_gate.py": {
        "DEFAULT_INPUT_FORM_SCAFFOLD_PATH": Path(
            "tests/human_rebuild_authorization_record_input_form_scaffold_report.json"
        ),
        "DEFAULT_OUTPUT_PATH": Path("tests/human_rebuild_authorization_record_input_form_scaffold_gate_report.json"),
    },
    "tools/build_production_rebuild_readiness_cutoff.py": {
        "DEFAULT_SOURCE_PATCH_PATH": Path("tests/ingestion_metadata_source_patch_report.json"),
        "DEFAULT_DRY_RUN_PATH": Path("tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json"),
        "DEFAULT_DRY_RUN_GATE_PATH": Path(
            "tests/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json"
        ),
        "DEFAULT_OUTPUT_PATH": Path("tests/production_rebuild_readiness_cutoff_report.json"),
    },
    "tools/build_production_rebuild_live_preflight_runner_design.py": {
        "DEFAULT_READINESS_CUTOFF_PATH": Path("tests/production_rebuild_readiness_cutoff_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/production_rebuild_live_preflight_runner_design_report.json"),
    },
    "tools/check_production_rebuild_live_preflight_runner_design_gate.py": {
        "DEFAULT_DESIGN_PATH": Path("tests/production_rebuild_live_preflight_runner_design_report.json"),
        "DEFAULT_OUTPUT_PATH": Path("tests/production_rebuild_live_preflight_runner_design_gate_report.json"),
    },
    "tools/build_production_rebuild_live_preflight_runner_minimal_implementation_design.py": {
        "DEFAULT_DESIGN_GATE_PATH": Path("tests/production_rebuild_live_preflight_runner_design_gate_report.json"),
        "DEFAULT_OUTPUT_PATH": Path(
            "tests/production_rebuild_live_preflight_runner_minimal_implementation_design_report.json"
        ),
    },
    "tools/check_production_rebuild_live_preflight_runner_minimal_implementation_design_gate.py": {
        "DEFAULT_DESIGN_PATH": Path(
            "tests/production_rebuild_live_preflight_runner_minimal_implementation_design_report.json"
        ),
        "DEFAULT_OUTPUT_PATH": Path(
            "tests/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json"
        ),
    },
    "tools/build_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py": {
        "DEFAULT_IMPLEMENTATION_DESIGN_GATE_PATH": Path(
            "tests/production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json"
        ),
        "DEFAULT_OUTPUT_PATH": Path(
            "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json"
        ),
    },
    "tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py": {
        "DEFAULT_DESIGN_PATH": Path(
            "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json"
        ),
        "DEFAULT_OUTPUT_PATH": Path(
            "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_report.json"
        ),
    },
    "tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py": {
        "DEFAULT_SCAFFOLD_REPORT_PATH": Path(
            "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json"
        ),
        "DEFAULT_OUTPUT_PATH": Path(
            "tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_report.json"
        ),
    },
    "tools/run_production_rebuild_live_preflight_real_readonly_probe.py": {
        "DEFAULT_OUTPUT_PATH": Path("tests/production_rebuild_live_preflight_real_readonly_probe_report.json"),
    },
    "tools/run_production_rebuild_live_preflight_snapshot_reference_probe.py": {
        "DEFAULT_OUTPUT_PATH": Path("tests/production_rebuild_live_preflight_snapshot_reference_probe_report.json"),
    },
    "tools/run_production_rebuild_live_preflight_snapshot_create_reference_capture.py": {
        "DEFAULT_OUTPUT_PATH": Path(
            "tests/production_rebuild_live_preflight_snapshot_create_reference_capture_report.json"
        ),
    },
    "tools/check_production_rebuild_formal_authorization_gate.py": {
        "DEFAULT_OUTPUT_PATH": Path("tests/production_rebuild_formal_authorization_gate_report.json"),
    },
}


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def compile_checks(paths: list[Path]) -> list[dict[str, Any]]:
    results = []
    for path in paths:
        result: dict[str, Any] = {
            "path": str(path),
            "status": "passed",
            "method": "builtin_compile_no_pyc",
        }
        try:
            source = path.read_text(encoding="utf-8-sig")
            compile(source, str(path), "exec")
        except Exception as exc:  # pragma: no cover - exact compiler errors are environment-specific.
            result = {
                "path": str(path),
                "status": "failed",
                "method": "builtin_compile_no_pyc",
                "error": str(exc),
            }
        results.append(result)
    return results


def report_presence_checks(paths: list[Path]) -> list[dict[str, Any]]:
    results = []
    for path in paths:
        data = read_json(path)
        results.append({
            "path": str(path),
            "status": "passed" if path.exists() and isinstance(data, dict) else "failed",
            "present": path.exists(),
            "version": data.get("version") if isinstance(data, dict) else None,
            "scope": data.get("scope") if isinstance(data, dict) else None,
            "schema_kind": data.get("schema_kind") if isinstance(data, dict) else None,
        })
    return results


def scaffold_directory_checks(paths: list[Path]) -> list[dict[str, Any]]:
    results = []
    for path in paths:
        is_directory = path.is_dir()
        results.append({
            "path": str(path),
            "status": "passed" if is_directory else "failed",
            "present": path.exists(),
            "is_directory": is_directory,
        })
    return results


def scaffold_purity_check(roots: list[Path], allowed_files: set[Path]) -> dict[str, Any]:
    allowed = {path.resolve() for path in allowed_files}
    missing_roots = []
    unexpected_files = []
    for root in roots:
        if not root.exists():
            missing_roots.append(str(root))
            continue
        for path in root.rglob("*"):
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if path.is_file() and path.resolve() not in allowed:
                unexpected_files.append(str(path))
    status = "passed" if not missing_roots and not unexpected_files else "failed"
    return {
        "status": status,
        "scope": "scaffold_only_current_maintenance",
        "roots": [str(path) for path in roots],
        "missing_roots": sorted(missing_roots),
        "unexpected_files": sorted(unexpected_files),
        "allowed_files": sorted(str(path) for path in allowed_files),
    }


def anchor_presence_check(path: Path, required_anchors: list[str]) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    missing_anchors = [anchor for anchor in required_anchors if anchor not in content]
    return {
        "path": str(path),
        "status": "passed" if path.exists() and not missing_anchors else "failed",
        "present": path.exists(),
        "required_anchors": required_anchors,
        "missing_anchors": missing_anchors,
    }


def artifact_index_check(path: Path, required_anchors: list[str]) -> dict[str, Any]:
    return anchor_presence_check(path, required_anchors)


def tool_index_check(path: Path, required_anchors: list[str]) -> dict[str, Any]:
    return anchor_presence_check(path, required_anchors)


def encoding_hygiene_report_check(path: Path) -> dict[str, Any]:
    data = read_json(path)
    summary = data.get("summary") if isinstance(data, dict) and isinstance(data.get("summary"), dict) else {}
    guardrails = data.get("guardrails") if isinstance(data, dict) and isinstance(data.get("guardrails"), dict) else {}
    errors = []
    if not path.exists():
        errors.append("missing_report")
    if summary.get("status") != "passed":
        errors.append("encoding_hygiene_status_not_passed")
    if summary.get("utf8_error_count", 0) != 0:
        errors.append("utf8_errors_detected")
    if summary.get("error_count", 0) != 0:
        errors.append("encoding_errors_detected")
    if guardrails.get("scanned_files_are_not_modified") is not True:
        errors.append("missing_non_mutation_guardrail")
    if guardrails.get("file_delete_or_move") != "not_performed":
        errors.append("missing_no_delete_or_move_guardrail")
    return {
        "path": str(path),
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "summary": summary,
    }


def tool_index_consistency_report_check(path: Path) -> dict[str, Any]:
    data = read_json(path)
    summary = data.get("summary") if isinstance(data, dict) and isinstance(data.get("summary"), dict) else {}
    guardrails = data.get("guardrails") if isinstance(data, dict) and isinstance(data.get("guardrails"), dict) else {}
    errors = []
    if not path.exists():
        errors.append("missing_report")
    if summary.get("status") != "passed":
        errors.append("tool_index_consistency_status_not_passed")
    if summary.get("missing_tool_count", 0) != 0:
        errors.append("tool_index_missing_tools_detected")
    if summary.get("missing_boundary_anchor_count", 0) != 0:
        errors.append("tool_index_boundary_anchors_missing")
    if guardrails.get("scanned_files_are_not_modified") is not True:
        errors.append("missing_non_mutation_guardrail")
    if guardrails.get("tool_move_or_rename") != "not_performed":
        errors.append("missing_no_tool_move_guardrail")
    return {
        "path": str(path),
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "summary": summary,
    }


def test_index_consistency_report_check(path: Path) -> dict[str, Any]:
    data = read_json(path)
    summary = data.get("summary") if isinstance(data, dict) and isinstance(data.get("summary"), dict) else {}
    guardrails = data.get("guardrails") if isinstance(data, dict) and isinstance(data.get("guardrails"), dict) else {}
    errors = []
    if not path.exists():
        errors.append("missing_report")
    if summary.get("status") != "passed":
        errors.append("test_index_consistency_status_not_passed")
    if summary.get("missing_test_count", 0) != 0:
        errors.append("test_index_missing_tests_detected")
    if summary.get("missing_required_anchor_count", 0) != 0:
        errors.append("test_index_required_anchors_missing")
    if guardrails.get("scanned_files_are_not_modified") is not True:
        errors.append("missing_non_mutation_guardrail")
    if guardrails.get("test_move_or_rename") != "not_performed":
        errors.append("missing_no_test_move_guardrail")
    return {
        "path": str(path),
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "summary": summary,
    }


def artifact_index_consistency_report_check(path: Path) -> dict[str, Any]:
    data = read_json(path)
    summary = data.get("summary") if isinstance(data, dict) and isinstance(data.get("summary"), dict) else {}
    guardrails = data.get("guardrails") if isinstance(data, dict) and isinstance(data.get("guardrails"), dict) else {}
    errors = []
    if not path.exists():
        errors.append("missing_report")
    if summary.get("status") != "passed":
        errors.append("artifact_index_consistency_status_not_passed")
    if summary.get("missing_artifact_count", 0) != 0:
        errors.append("artifact_index_missing_artifacts_detected")
    if summary.get("missing_required_anchor_count", 0) != 0:
        errors.append("artifact_index_required_anchors_missing")
    if summary.get("missing_semantic_guardrail_count", 0) != 0:
        errors.append("artifact_index_semantic_guardrails_missing")
    if guardrails.get("scanned_files_are_not_modified") is not True:
        errors.append("missing_non_mutation_guardrail")
    if guardrails.get("report_move_or_migration") != "not_performed":
        errors.append("missing_no_report_migration_guardrail")
    return {
        "path": str(path),
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "summary": summary,
    }


def layout_migration_readiness_report_check(path: Path) -> dict[str, Any]:
    data = read_json(path)
    summary = data.get("summary") if isinstance(data, dict) and isinstance(data.get("summary"), dict) else {}
    guardrails = data.get("guardrails") if isinstance(data, dict) and isinstance(data.get("guardrails"), dict) else {}
    errors = []
    if not path.exists():
        errors.append("missing_report")
    if summary.get("status") != "ready_for_planning":
        errors.append("layout_migration_readiness_not_ready_for_planning")
    if summary.get("ready_for_automatic_migration") is not False:
        errors.append("layout_migration_auto_migration_not_blocked")
    if summary.get("blocker_count", 0) != 0:
        errors.append("layout_migration_blockers_detected")
    if guardrails.get("scanned_files_are_not_modified") is not True:
        errors.append("missing_non_mutation_guardrail")
    if guardrails.get("file_move_or_migration") != "not_performed":
        errors.append("missing_no_file_migration_guardrail")
    return {
        "path": str(path),
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "summary": summary,
    }


def maintenance_closeout_report_check(path: Path) -> dict[str, Any]:
    data = read_json(path)
    summary = data.get("summary") if isinstance(data, dict) and isinstance(data.get("summary"), dict) else {}
    guardrails = data.get("guardrails") if isinstance(data, dict) and isinstance(data.get("guardrails"), dict) else {}
    errors = []
    if not path.exists():
        errors.append("missing_report")
    if summary.get("status") != "passed":
        errors.append("maintenance_closeout_status_not_passed")
    if summary.get("layout_migration") != "not_performed":
        errors.append("maintenance_closeout_layout_migration_not_blocked")
    if summary.get("rag_main_flow_change") != "not_performed":
        errors.append("maintenance_closeout_rag_flow_changed")
    if guardrails.get("scanned_files_are_not_modified") is not True:
        errors.append("missing_non_mutation_guardrail")
    if guardrails.get("file_move_or_migration") != "not_performed":
        errors.append("missing_no_file_migration_guardrail")
    return {
        "path": str(path),
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "summary": summary,
    }


def layout_compatibility_check(report_pairs: list[tuple[str, str]]) -> dict[str, Any]:
    contract = compatibility_contract()
    resolutions = []
    errors = []
    for legacy_path, group in report_pairs:
        try:
            resolution = resolve_report_pair(legacy_path, group)
        except Exception as exc:  # pragma: no cover - defensive report coverage.
            errors.append({"legacy_path": legacy_path, "group": group, "error": str(exc)})
            continue
        resolutions.append({
            "artifact_name": resolution.artifact_name,
            "group": group,
            "legacy_path": str(resolution.legacy_path),
            "future_path": str(resolution.future_path),
            "selected_path": str(resolution.selected_path),
            "selected_source": resolution.selected_source,
            "legacy_authoritative": resolution.legacy_authoritative,
            "migration_performed": resolution.migration_performed,
        })
    contract_ok = (
        contract.get("legacy_report_paths_authoritative") is True
        and contract.get("future_report_paths_are_mirrors_only") is True
        and contract.get("automatic_migration") is False
        and contract.get("tool_entrypoint_migration") is False
    )
    mappings_ok = all(
        row["selected_path"] == row["legacy_path"]
        and row["selected_source"] == "legacy_tests"
        and row["legacy_authoritative"] is True
        and row["migration_performed"] is False
        for row in resolutions
    )
    return {
        "status": "passed" if contract_ok and mappings_ok and not errors else "failed",
        "contract": contract,
        "resolutions": resolutions,
        "errors": errors,
    }


def layout_helper_pilot_checks(expected_defaults: dict[str, dict[str, Path]]) -> list[dict[str, Any]]:
    results = []
    for tool_path, defaults in expected_defaults.items():
        module_name = ".".join(Path(tool_path).with_suffix("").parts)
        module = __import__(module_name, fromlist=list(defaults))
        mismatches = []
        for name, expected in defaults.items():
            actual = getattr(module, name, None)
            if actual != expected:
                mismatches.append({
                    "constant": name,
                    "expected": str(expected),
                    "actual": str(actual),
                })
        results.append({
            "path": tool_path,
            "status": "passed" if not mismatches else "failed",
            "uses_layout_helper": "legacy_report_path(" in Path(tool_path).read_text(encoding="utf-8"),
            "defaults_remain_legacy_tests": not mismatches,
            "mismatches": mismatches,
        })
    return results


def dry_run_artifact_contract_check() -> dict[str, Any]:
    from tools.build_manual_review_export_pipeline_dry_run import DEFAULT_ARTIFACT_DIR

    expected = Path("tests/manual_review_export_pipeline_dry_run_artifacts")
    errors = []
    if DEFAULT_ARTIFACT_DIR != expected:
        errors.append("artifact_dir_default_changed")
    if DEFAULT_ARTIFACT_DIR.parts and DEFAULT_ARTIFACT_DIR.parts[0] == "reports":
        errors.append("artifact_dir_redirected_to_reports")
    return {
        "path": str(DEFAULT_ARTIFACT_DIR),
        "status": "passed" if not errors else "failed",
        "expected": str(expected),
        "remains_isolated_tests_artifact_dir": DEFAULT_ARTIFACT_DIR == expected,
        "not_mapped_to_reports": not (DEFAULT_ARTIFACT_DIR.parts and DEFAULT_ARTIFACT_DIR.parts[0] == "reports"),
        "errors": errors,
    }


def advisory_boundary_checks(paths: list[Path]) -> list[dict[str, Any]]:
    results = []
    for path in paths:
        data = read_json(path)
        matched_keys = Counter()
        for node in walk_dicts(data):
            matched_keys.update(FORBIDDEN_IMPORT_KEYS & set(node.keys()))
        summary = data.get("summary") if isinstance(data, dict) and isinstance(data.get("summary"), dict) else {}
        status = "passed"
        errors = []
        if not path.exists():
            status = "failed"
            errors.append("missing_report")
        if matched_keys:
            status = "failed"
            errors.append("contains_importable_or_completed_review_keys")
        if data.get("advisory_packet_only") is not True:
            status = "failed"
            errors.append("advisory_packet_only_not_true")
        if data.get("contains_completed_manual_decisions") is not False:
            status = "failed"
            errors.append("contains_completed_manual_decisions_not_false")
        if summary.get("completed_manual_decisions", 0) != 0:
            status = "failed"
            errors.append("completed_manual_decisions_nonzero")
        results.append({
            "path": str(path),
            "status": status,
            "errors": errors,
            "matched_forbidden_keys": dict(sorted(matched_keys.items())),
        })
    return results


def offline_pattern_checks(paths: list[Path]) -> list[dict[str, Any]]:
    results = []
    for path in paths:
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        matches = sorted(pattern for pattern in PROHIBITED_OFFLINE_PATTERNS if pattern in content)
        results.append({
            "path": str(path),
            "status": "failed" if matches else "passed",
            "matches": matches,
        })
    return results


def version_consistency_check() -> dict[str, Any]:
    main_path = Path("src/main.py")
    content = main_path.read_text(encoding="utf-8") if main_path.exists() else ""
    match = re.search(r'FastAPI\(title="[^"]+", version="([^"]+)"\)', content)
    main_version = match.group(1) if match else None
    return {
        "path": str(main_path),
        "status": "passed" if main_version == VERSION else "failed",
        "expected_version": VERSION,
        "actual_version": main_version,
    }


def summarize(sections: dict[str, Any]) -> dict[str, Any]:
    failed = []
    total_checks = 0
    for section, value in sections.items():
        rows = value if isinstance(value, list) else [value]
        for row in rows:
            if not isinstance(row, dict) or "status" not in row:
                continue
            total_checks += 1
            if row["status"] != "passed":
                failed.append({"section": section, **row})
    return {
        "status": "passed" if not failed else "failed",
        "total_checks": total_checks,
        "failed_checks": len(failed),
        "failed": failed,
    }


def build_sections() -> dict[str, Any]:
    return {
        "syntax_compile": compile_checks(SYNTAX_CHECK_TARGETS),
        "required_reports": report_presence_checks(REQUIRED_REPORTS),
        "scaffold_directory_presence": scaffold_directory_checks(REQUIRED_SCAFFOLD_DIRECTORIES),
        "scaffold_purity": scaffold_purity_check(SCAFFOLD_PURITY_ROOTS, SCAFFOLD_ALLOWED_FILES),
        "artifact_index": artifact_index_check(ARTIFACT_INDEX_PATH, ARTIFACT_INDEX_REQUIRED_ANCHORS),
        "tool_index": tool_index_check(TOOL_INDEX_PATH, TOOL_INDEX_REQUIRED_ANCHORS),
        "test_index": anchor_presence_check(TEST_INDEX_PATH, TEST_INDEX_REQUIRED_ANCHORS),
        "encoding_hygiene_report": encoding_hygiene_report_check(ENCODING_HYGIENE_REPORT_PATH),
        "tool_index_consistency_report": tool_index_consistency_report_check(TOOL_INDEX_CONSISTENCY_REPORT_PATH),
        "test_index_consistency_report": test_index_consistency_report_check(TEST_INDEX_CONSISTENCY_REPORT_PATH),
        "artifact_index_consistency_report": artifact_index_consistency_report_check(ARTIFACT_INDEX_CONSISTENCY_REPORT_PATH),
        "layout_migration_readiness_report": layout_migration_readiness_report_check(LAYOUT_MIGRATION_READINESS_REPORT_PATH),
        "maintenance_closeout_report": maintenance_closeout_report_check(MAINTENANCE_CLOSEOUT_REPORT_PATH),
        "layout_compatibility": layout_compatibility_check(LAYOUT_COMPATIBILITY_REPORTS),
        "layout_helper_pilot_defaults": layout_helper_pilot_checks(LAYOUT_HELPER_PILOT_DEFAULTS),
        "dry_run_artifact_contract": dry_run_artifact_contract_check(),
        "advisory_boundaries": advisory_boundary_checks(ADVISORY_REPORTS),
        "offline_pattern_scan": offline_pattern_checks(OFFLINE_TOOL_TARGETS),
        "version_consistency": version_consistency_check(),
    }


def build_report() -> dict[str, Any]:
    sections = build_sections()
    return {
        "version": VERSION,
        "scope": "project health check for offline RAG governance tooling",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "guardrails": {
            "runtime_state_mutation": "disallowed",
            "writes_health_report": True,
            "syntax_check_bytecode": "not_written",
            "full_eval": "not_run",
            "rag_query_integration": "disallowed",
            "backend_api_write": "disallowed",
            "qdrant_access": "disallowed",
            "llm_access": "disallowed",
            "hidden_seed_mutation": "disallowed",
            "anchor_mutation": "disallowed",
            "rerank_mutation": "disallowed",
            "prompt_mutation": "disallowed",
            "risk_rule_mutation": "disallowed",
            "risk_supplement_mutation": "disallowed",
            "term_preservation_rule_mutation": "disallowed",
            "scenario_registry_mutation": "disallowed",
            "eval_case_mutation": "disallowed",
            "fixture_mutation": "disallowed",
            "schema_mutation": "disallowed",
            "manual_review_schema_mutation": "disallowed",
            "manual_review_importer_mutation": "disallowed",
            "manual_review_dry_run_contract_mutation": "disallowed",
        },
        "summary": summarize(sections),
        **sections,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run lightweight project health checks.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-error", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report()
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Project health check completed: "
        f"{summary['status']}, "
        f"{summary['total_checks']} checks, "
        f"{summary['failed_checks']} failed"
    )
    return 1 if args.fail_on_error and summary["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
