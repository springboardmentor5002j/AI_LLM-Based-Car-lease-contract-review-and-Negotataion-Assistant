import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
class UploadScreen extends StatefulWidget {
  @override
  _UploadScreenState createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  String result = "";

  Future<void> uploadFile() async {
    var picked = await FilePicker.platform.pickFiles();

    if (picked == null) return;

    var fileBytes = picked.files.single.bytes;
    var fileName = picked.files.single.name;

    var request = http.MultipartRequest(
      'POST',
      Uri.parse('http://127.0.0.1:5000/analyze'),
    );

    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        fileBytes!,
        filename: fileName,
      ),
    );

    var response = await request.send();
    var res = await response.stream.bytesToString();

    setState(() {
      result = res;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Car Lease Analyzer")),
      body: Column(
        children: [
          ElevatedButton(
            onPressed: uploadFile,
            child: Text("Upload Contract"),
          ),
          Expanded(
            child: SingleChildScrollView(
              child: Text(result),
            ),
          )
        ],
      ),
    );
  }
}