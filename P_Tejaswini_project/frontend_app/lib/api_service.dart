import 'package:http/http.dart' as http;
import 'dart:convert';
import 'models.dart';

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:5000';

  static Future<AnalysisResponse> analyzeContract(List<int> fileBytes, String fileName) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/analyze'),
      );

      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          fileBytes,
          filename: fileName,
        ),
      );

      var response = await request.send();
      var responseBody = await response.stream.bytesToString();

      if (response.statusCode == 200) {
        final json = jsonDecode(responseBody);
        return AnalysisResponse.fromJson(json);
      } else {
        throw Exception('Failed to analyze contract: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error analyzing contract: $e');
    }
  }

  static Future<bool> checkBackendHealth() async {
    try {
      var response = await http.get(
        Uri.parse('$baseUrl/'),
        headers: {'Content-Type': 'application/json'},
      ).timeout(Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
