import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'models.dart';
import 'api_service.dart';

// SCREEN 1: Upload Contract
class UploadScreen extends StatefulWidget {
  @override
  _UploadScreenState createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  String? fileName;
  List<int>? fileBytes;
  bool isLoading = false;
  String? error;

  Future<void> pickFile() async {
    try {
      var picked = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
      );

      if (picked != null) {
        setState(() {
          fileName = picked.files.single.name;
          fileBytes = picked.files.single.bytes;
          error = null;
        });
      }
    } catch (e) {
      setState(() {
        error = 'Error picking file: $e';
      });
    }
  }

  Future<void> uploadAndAnalyze() async {
    if (fileBytes == null || fileName == null) {
      setState(() {
        error = 'Please select a PDF file';
      });
      return;
    }

    setState(() {
      isLoading = true;
      error = null;
    });

    try {
      final result = await ApiService.analyzeContract(fileBytes!, fileName!);
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => ResultsScreen(analysisResult: result),
          ),
        );
      }
    } catch (e) {
      setState(() {
        error = 'Error: ${e.toString()}';
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Car Lease Analyzer'),
        centerTitle: true,
        backgroundColor: Colors.blueAccent,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: EdgeInsets.all(20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.description, size: 80, color: Colors.blueAccent),
              SizedBox(height: 20),
              Text(
                'Upload Your Lease Contract',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              SizedBox(height: 10),
              Text(
                'Select a PDF file to analyze SLA terms and vehicle info',
                style: TextStyle(fontSize: 14, color: Colors.grey),
                textAlign: TextAlign.center,
              ),
              SizedBox(height: 30),
              if (fileName != null)
                Container(
                  padding: EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.green[50],
                    border: Border.all(color: Colors.green),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.check_circle, color: Colors.green),
                      SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          fileName!,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(color: Colors.green[700]),
                        ),
                      ),
                    ],
                  ),
                ),
              SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: isLoading ? null : pickFile,
                icon: Icon(Icons.attach_file),
                label: Text('Choose PDF File'),
                style: ElevatedButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: 30, vertical: 15),
                  backgroundColor: Colors.blueAccent,
                ),
              ),
              SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: isLoading ? null : uploadAndAnalyze,
                icon: isLoading
                    ? SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : Icon(Icons.cloud_upload),
                label: Text(isLoading ? 'Analyzing...' : 'Analyze Contract'),
                style: ElevatedButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: 30, vertical: 15),
                  backgroundColor: Colors.green,
                ),
              ),
              if (error != null) ...[
                SizedBox(height: 20),
                Container(
                  padding: EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.red[50],
                    border: Border.all(color: Colors.red),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.error, color: Colors.red),
                      SizedBox(width: 10),
                      Expanded(child: Text(error!, style: TextStyle(color: Colors.red))),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

// SCREEN 2: Results - SLA Data Display
class ResultsScreen extends StatelessWidget {
  final AnalysisResponse analysisResult;

  ResultsScreen({required this.analysisResult});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Lease Agreement Terms'),
        centerTitle: true,
        backgroundColor: Colors.blue[800],
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Extracted SLA Terms',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 16),
            SLACard(
              title: 'Annual Percentage Rate (APR)',
              value: analysisResult.sla.apr,
              icon: Icons.percent,
              color: Colors.orange,
            ),
            SLACard(
              title: 'Lease Term',
              value: analysisResult.sla.term,
              icon: Icons.calendar_today,
              color: Colors.blue,
            ),
            SLACard(
              title: 'Monthly Payment',
              value: '\$${analysisResult.sla.monthlyPayment}',
              icon: Icons.payments,
              color: Colors.green,
            ),
            SLACard(
              title: 'Down Payment',
              value: '\$${analysisResult.sla.downPayment}',
              icon: Icons.account_balance_wallet,
              color: Colors.purple,
            ),
            SLACard(
              title: 'Annual Mileage Allowance',
              value: '${analysisResult.sla.annualMileage} miles',
              icon: Icons.directions_car,
              color: Colors.red,
            ),
            SizedBox(height: 24),
            ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => VehicleScreen(analysisResult: analysisResult),
                  ),
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue[600],
                minimumSize: Size(double.infinity, 50),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.directions_car),
                  SizedBox(width: 10),
                  Text('View Vehicle Info'),
                ],
              ),
            ),
            SizedBox(height: 12),
            ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => SuggestionsScreen(analysisResult: analysisResult),
                  ),
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.amber[600],
                minimumSize: Size(double.infinity, 50),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.lightbulb),
                  SizedBox(width: 10),
                  Text('Negotiation Suggestions'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// SCREEN 3: Vehicle Info Display
class VehicleScreen extends StatelessWidget {
  final AnalysisResponse analysisResult;

  VehicleScreen({required this.analysisResult});

  @override
  Widget build(BuildContext context) {
    final vehicle = analysisResult.vehicle;

    return Scaffold(
      appBar: AppBar(
        title: Text('Vehicle Information'),
        centerTitle: true,
        backgroundColor: Colors.teal,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'VIN: ${analysisResult.sla.vin}',
              style: TextStyle(fontSize: 14, color: Colors.grey),
            ),
            SizedBox(height: 20),
            if (vehicle.containsKey('error'))
              Card(
                color: Colors.red[50],
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Icon(Icons.info, color: Colors.red),
                      SizedBox(width: 10),
                      Expanded(child: Text(vehicle['error'])),
                    ],
                  ),
                ),
              )
            else ...[
              VehicleInfoCard(
                title: 'Make',
                value: vehicle['Make'] ?? 'N/A',
                icon: Icons.badge,
              ),
              VehicleInfoCard(
                title: 'Model',
                value: vehicle['Model'] ?? 'N/A',
                icon: Icons.directions_car,
              ),
              VehicleInfoCard(
                title: 'Model Year',
                value: vehicle['Model Year'] ?? 'N/A',
                icon: Icons.calendar_today,
              ),
              VehicleInfoCard(
                title: 'Body Class',
                value: vehicle['Body Class'] ?? 'N/A',
                icon: Icons.inventory_2,
              ),
              VehicleInfoCard(
                title: 'Engine Displacement',
                value: vehicle['Engine Displacement (cc)'] ?? 'N/A',
                icon: Icons.settings,
              ),
            ],
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.teal,
                minimumSize: Size(double.infinity, 50),
              ),
              child: Text('Back'),
            ),
          ],
        ),
      ),
    );
  }
}

// SCREEN 4: Negotiation Chatbot UI
class SuggestionsScreen extends StatefulWidget {
  final AnalysisResponse analysisResult;

  SuggestionsScreen({required this.analysisResult});

  @override
  _SuggestionsScreenState createState() => _SuggestionsScreenState();
}

class _SuggestionsScreenState extends State<SuggestionsScreen> {
  late List<ChatMessage> messages;
  TextEditingController messageController = TextEditingController();

  @override
  void initState() {
    super.initState();
    messages = [
      ChatMessage(
        text:
            'Hi! I\'ve analyzed your lease contract. Here are my suggestions:',
        isBot: true,
      ),
      ...widget.analysisResult.suggestions
          .map((s) => ChatMessage(text: s, isBot: true))
          .toList(),
      ChatMessage(
        text: 'Feel free to ask me any questions about the terms!',
        isBot: true,
      ),
    ];
  }

  void sendMessage() {
    if (messageController.text.isEmpty) return;

    setState(() {
      messages.add(ChatMessage(text: messageController.text, isBot: false));
    });

    messageController.clear();

    Future.delayed(Duration(milliseconds: 500), () {
      if (mounted) {
        setState(() {
          messages.add(
            ChatMessage(
              text: getBotResponse(messages.last.text),
              isBot: true,
            ),
          );
        });
      }
    });
  }

  String getBotResponse(String userMessage) {
    final lower = userMessage.toLowerCase();

    if (lower.contains('apr') || lower.contains('rate')) {
      return 'The APR in your contract is ${widget.analysisResult.sla.apr}%. Try negotiating for a lower rate if possible.';
    } else if (lower.contains('payment')) {
      return 'Your monthly payment is ${widget.analysisResult.sla.monthlyPayment}. Consider your budget carefully.';
    } else if (lower.contains('mileage') || lower.contains('miles')) {
      return 'Your annual mileage allowance is ${widget.analysisResult.sla.annualMileage} miles. Check if this suits your driving habits.';
    } else if (lower.contains('down payment')) {
      return 'Your down payment is ${widget.analysisResult.sla.downPayment}. Negotiate for lower down payment if possible.';
    } else if (lower.contains('term') || lower.contains('months')) {
      return 'Your lease term is ${widget.analysisResult.sla.term} months. Consider your needs for flexibility.';
    }

    return 'I understand your concern about the lease terms. Review all conditions carefully and don\'t hesitate to negotiate!';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Negotiation Assistant'),
        centerTitle: true,
        backgroundColor: Colors.indigo,
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              reverse: true,
              itemCount: messages.length,
              itemBuilder: (context, index) {
                final message = messages[messages.length - 1 - index];
                return ChatBubble(message: message);
              },
            ),
          ),
          Divider(height: 1),
          Padding(
            padding: EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: messageController,
                    decoration: InputDecoration(
                      hintText: 'Ask me a question...',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 12,
                      ),
                    ),
                  ),
                ),
                SizedBox(width: 8),
                FloatingActionButton(
                  onPressed: sendMessage,
                  backgroundColor: Colors.indigo,
                  child: Icon(Icons.send),
                  mini: true,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    messageController.dispose();
    super.dispose();
  }
}

// Helper Widgets

class SLACard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  SLACard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.only(bottom: 12),
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: color.withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(icon, color: color, size: 28),
            ),
            SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                  SizedBox(height: 4),
                  Text(
                    value,
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class VehicleInfoCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;

  VehicleInfoCard({
    required this.title,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(icon, color: Colors.teal, size: 24),
            SizedBox(width: 16),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: TextStyle(fontSize: 12, color: Colors.grey)),
                SizedBox(height: 4),
                Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class ChatMessage {
  final String text;
  final bool isBot;

  ChatMessage({required this.text, required this.isBot});
}

class ChatBubble extends StatelessWidget {
  final ChatMessage message;

  ChatBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: message.isBot ? Alignment.centerLeft : Alignment.centerRight,
      child: Container(
        margin: EdgeInsets.symmetric(vertical: 8, horizontal: 12),
        padding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: message.isBot ? Colors.grey[300] : Colors.blue,
          borderRadius: BorderRadius.circular(12),
        ),
        constraints: BoxConstraints(maxWidth: 250),
        child: Text(
          message.text,
          style: TextStyle(
            color: message.isBot ? Colors.black87 : Colors.white,
            fontSize: 14,
          ),
        ),
      ),
    );
  }
}
