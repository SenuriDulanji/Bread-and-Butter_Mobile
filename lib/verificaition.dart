import 'dart:async'; // For Timer
import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'login.dart'; // Replace with actual login screen import if needed
import 'config.dart'; // Import config for baseUrl

class VerificationPage extends StatefulWidget {
  final int userId;  // Add userId as a required parameter

  VerificationPage({required this.userId});

  @override
  _VerificationPageState createState() => _VerificationPageState();
}

class _VerificationPageState extends State<VerificationPage>
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<Offset> _slideAnimation;
  late Animation<double> _fadeAnimation;

  final TextEditingController _otpController = TextEditingController();
  late Timer _resendOtpTimer;
  int _remainingTime = 60;  // Time in seconds for the cooldown
  bool _isResendEnabled = true;

  @override
  void initState() {
    super.initState();
    // Initialize the animation controller and animations
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );

    _slideAnimation = Tween<Offset>(begin: const Offset(0, 1), end: Offset.zero)
        .animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOut,
    ));

    _fadeAnimation = Tween<double>(begin: 0, end: 1).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));

    // Start the animation
    _animationController.forward();
  }

  @override
  void dispose() {
    _resendOtpTimer.cancel(); // Cancel the timer when the widget is disposed
    _animationController.dispose();
    super.dispose();
  }

  Future<void> _verifyOTP() async {
    // Direct validation of OTP field before proceeding
    if (_otpController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('OTP is required.')),
      );
      return;
    }

    // Prepare the request body as JSON
    final body = jsonEncode({
      'user_id': widget.userId,  // Pass the user_id
      'otp_code': _otpController.text,  // OTP entered by the user
    });

    try {
      // Send POST request to the verify.php API endpoint
      final response = await http.post(
        Uri.parse('$baseUrl/verify'),  // Use the base URL for the API
        headers: {'Content-Type': 'application/json'},
        body: body,
      );

      // Decode the response
      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200) {
        if (responseData['success'] == true) {
          // OTP verification successful
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('OTP Verified Successfully!')),
          );

          // Navigate to HomePage after successful verification
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => LoginPage()),
          );
        } else {
          // OTP verification failed
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(responseData['message'])),
          );
        }
      } else {
        // Handle server errors or unsuccessful status code
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to verify OTP. Please try again later.')),
        );
      }
    } catch (e) {
      // Catch errors related to network or API issues
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('An error occurred. Please check your connection.')),
      );
    }
  }

  void _startResendOtpTimer() {
    setState(() {
      _isResendEnabled = false;
      _remainingTime = 60; // Reset timer to 60 seconds
    });

    // Start a timer to update the countdown
    _resendOtpTimer = Timer.periodic(Duration(seconds: 1), (timer) {
      if (_remainingTime == 0) {
        setState(() {
          _isResendEnabled = true;  // Enable button again
        });
        _resendOtpTimer.cancel();  // Stop the timer
      } else {
        setState(() {
          _remainingTime--;
        });
      }
    });
  }

  Future<void> _resendOTP() async {
    // Make API call to resend OTP here
    try {
      final body = jsonEncode({
        'user_id': widget.userId,  // Send user_id
      });

      final response = await http.post(
        Uri.parse('$baseUrl/resend_otp'),  // API endpoint to resend OTP
        headers: {'Content-Type': 'application/json'},
        body: body,
      );

      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200) {
        if (responseData['success'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('OTP Resent Successfully!')),
          );
          _startResendOtpTimer();  // Start timer after successful OTP resend
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(responseData['message'])),
          );
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to resend OTP. Please try again later.')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('An error occurred while resending OTP.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: true, // Adjusts for keyboard
      body: SingleChildScrollView(
        child: Container(
          height: MediaQuery.of(context).size.height, // Full screen size
          decoration: const BoxDecoration(
            image: DecorationImage(
              image: AssetImage("assets/login.png"), // Replace with your image path
              fit: BoxFit.cover,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 290), // Space to move "Verify" text down
              // Header with fade and slide animation
              FadeTransition(
                opacity: _fadeAnimation,
                child: SlideTransition(
                  position: _slideAnimation,
                  child: Text(
                    "Verify",
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: Colors.orange.shade900,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 10),
              // Header text with fade and slide animation
              FadeTransition(
                opacity: _fadeAnimation,
                child: SlideTransition(
                  position: _slideAnimation,
                  child: Text(
                    "Enter One Time Password",
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.orange.shade900,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 40),
              // OTP Input field with fade and slide animation
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 40.0),
                child: FadeTransition(
                  opacity: _fadeAnimation,
                  child: SlideTransition(
                    position: _slideAnimation,
                    child: Align(
                      alignment: Alignment.center,
                      child: SizedBox(
                        width: MediaQuery.of(context).size.width * 0.8, // Match width of the button
                        child: TextField(
                          controller: _otpController,
                          decoration: InputDecoration(
                            hintText: "One Time Password",
                            prefixIcon: Icon(Icons.lock, color: Colors.orange.shade900),
                            filled: true,
                            fillColor: Colors.orange[100],
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide.none,
                            ),
                            contentPadding: const EdgeInsets.symmetric(
                                vertical: 15.0, horizontal: 20.0), // Reduce height
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 30),
              FadeTransition(
                opacity: _fadeAnimation,
                child: SlideTransition(
                  position: _slideAnimation,
                  child: Align(
                    alignment: Alignment.center,
                    child: SizedBox(
                      width: MediaQuery.of(context).size.width * 0.8, // Match width of the text field
                      child: ElevatedButton(
                        onPressed: _verifyOTP,  // Trigger verifyOTP function on press
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.orange.shade900,
                          padding: const EdgeInsets.symmetric(vertical: 15.0), // Remove the excessive horizontal padding
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(30),
                          ),
                          textStyle: const TextStyle(color: Colors.white),
                        ),
                        child: const Text(
                          "Verify",
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 20),
              // Resend OTP text
              FadeTransition(
                opacity: _fadeAnimation,
                child: SlideTransition(
                  position: _slideAnimation,
                  child: TextButton(
                    onPressed: _isResendEnabled ? _resendOTP : null, // Disable button if cooldown is active
                    child: Text(
                      _isResendEnabled
                          ? "Didn't receive OTP? Resend"
                          : "Resend OTP in $_remainingTime seconds",
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.orange.shade900,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              // Already have an account? Login text
              TextButton(
                onPressed: () {
                  // Navigate to Login screen
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => LoginPage()),
                  );
                },
                child: FadeTransition(
                  opacity: _fadeAnimation,
                  child: SlideTransition(
                    position: _slideAnimation,
                    child: Text(
                      "Already have an account? Login",
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.orange.shade900,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
