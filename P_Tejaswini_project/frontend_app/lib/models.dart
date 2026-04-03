class AnalysisResponse {
  final bool success;
  final SLAData sla;
  final Map<String, dynamic> vehicle;
  final List<String> suggestions;
  final String extractedTextPreview;

  AnalysisResponse({
    required this.success,
    required this.sla,
    required this.vehicle,
    required this.suggestions,
    required this.extractedTextPreview,
  });

  factory AnalysisResponse.fromJson(Map<String, dynamic> json) {
    return AnalysisResponse(
      success: json['success'] ?? false,
      sla: SLAData.fromJson(json['sla'] ?? {}),
      vehicle: json['vehicle'] ?? {},
      suggestions: List<String>.from(json['suggestions'] ?? []),
      extractedTextPreview: json['extracted_text_preview'] ?? '',
    );
  }
}

class SLAData {
  final String apr;
  final String term;
  final String monthlyPayment;
  final String downPayment;
  final String annualMileage;
  final String vin;

  SLAData({
    required this.apr,
    required this.term,
    required this.monthlyPayment,
    required this.downPayment,
    required this.annualMileage,
    required this.vin,
  });

  factory SLAData.fromJson(Map<String, dynamic> json) {
    return SLAData(
      apr: json['apr']?.toString() ?? 'Not found',
      term: json['term']?.toString() ?? 'Not found',
      monthlyPayment: json['monthly_payment']?.toString() ?? 'Not found',
      downPayment: json['down_payment']?.toString() ?? 'Not found',
      annualMileage: json['annual_mileage']?.toString() ?? 'Not found',
      vin: json['vin']?.toString() ?? 'Not found',
    );
  }
}
