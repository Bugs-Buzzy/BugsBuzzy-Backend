import json
import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock

User = get_user_model()


class AuthenticationFlowTestCase(APITestCase):
    """Test the complete authentication flow from signup to profile access"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.profile_url = reverse('profile')
        self.verify_url = reverse('verify_email')
        self.send_code_url = reverse('send_verification_code')
        self.refresh_url = reverse('token_refresh')
        
        # Test user data
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User',
            'national_code': '1234567890',
            'phone_number': '09123456789',
            'gender': 'M',
            'city': 'Tehran',
            'university': 'Test University',
            'major': 'Computer Science'
        }
    
    @patch('accounts.serializers.send_verification_email')
    def test_complete_signup_flow(self, mock_send_email):
        """Test complete signup process"""
        mock_send_email.return_value = True
        
        # Test signup
        response = self.client.post(self.signup_url, self.user_data, format='json')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['message'], 'User created successfully')
        
        # Verify user was created
        user = User.objects.get(email='test@example.com')
        self.assertFalse(user.is_verified)
        self.assertEqual(user.status, 'pending_verification')
        self.assertIsNotNone(user.verification_code)
        
        # Verify email was sent
        mock_send_email.assert_called_once()
    
    def test_signup_with_invalid_data(self):
        """Test signup with invalid data"""
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = self.client.post(self.signup_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_signup_with_existing_email(self):
        """Test signup with existing email"""
        # Create user first
        User.objects.create_user(
            email='test@example.com',
            username='existing',
            password='password123'
        )
        
        response = self.client.post(self.signup_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_login_with_valid_credentials(self):
        """Test login with valid credentials"""
        # Create and verify user
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        user.is_verified = True
        user.status = 'verified'
        user.save()
        
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['message'], 'Login successful')
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            'email': 'test@example.com',
            'password': 'WrongPassword'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_profile_access_without_authentication(self):
        """Test profile access without authentication"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_profile_access_without_verification(self):
        """Test profile access without email verification"""
        # Create unverified user
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Try to access profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_profile_access_with_verification(self):
        """Test profile access after email verification"""
        # Create and verify user
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        user.is_verified = True
        user.status = 'verified'
        user.save()
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Access profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertTrue(response.data['is_verified'])
    
    def test_profile_update(self):
        """Test profile update functionality"""
        # Create and verify user
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        user.is_verified = True
        user.status = 'verified'
        user.save()
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Update profile
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '09123456789',
            'gender': 'M',
            'city': 'Isfahan'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.put(self.profile_url, update_data, format='json')
        
        # Debug: Print response data if test fails
        if response.status_code != status.HTTP_200_OK:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Profile updated successfully')
        
        # Verify changes
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Name')
        self.assertEqual(user.city, 'Isfahan')
    
    @patch('accounts.views.send_verification_email')
    def test_send_verification_code(self, mock_send_email):
        """Test sending verification code"""
        mock_send_email.return_value = True
        
        # Create unverified user
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Send verification code
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.send_code_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_send_email.assert_called_once()
        
        # Verify user's try_count increased
        user.refresh_from_db()
        self.assertEqual(user.try_count, 1)
    
    def test_send_verification_code_already_verified(self):
        """Test sending verification code to already verified user"""
        # Create verified user
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        user.is_verified = True
        user.status = 'verified'
        user.save()
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Try to send verification code
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.send_code_url)
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['message'], 'User already verified')
    
    def test_verify_email_with_valid_code(self):
        """Test email verification with valid code"""
        # Create user with verification code
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        user.verification_code = 123456
        user.save()
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Verify email
        verify_data = {'verification_code': '123456'}
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.verify_url, verify_data, format='json')
        
        # Debug: Print response data if test fails
        if response.status_code != status.HTTP_200_OK:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
            print(f"User verification code: {user.verification_code}")
            print(f"User code updated at: {user.code_updated_at}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'User verified successfully')
        
        # Verify user is now verified
        user.refresh_from_db()
        self.assertTrue(user.is_verified)
        self.assertEqual(user.status, 'verified')
        self.assertIsNotNone(user.email_verified_at)
    
    def test_verify_email_with_invalid_code(self):
        """Test email verification with invalid code"""
        # Create user with verification code
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        user.verification_code = 123456
        user.save()
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Try to verify with wrong code
        verify_data = {'verification_code': '999999'}
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.verify_url, verify_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(response.data['message'], 'Verification Code is not correct')
    
    def test_token_refresh(self):
        """Test JWT token refresh functionality"""
        # Create user
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        
        # Get refresh token
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)
        
        # Refresh access token
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(self.refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
        # Verify new access token works
        new_access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        
        # Try to access profile (should fail without verification)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_token_refresh_with_invalid_token(self):
        """Test token refresh with invalid refresh token"""
        refresh_data = {'refresh': 'invalid_token'}
        response = self.client.post(self.refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error'], 'Invalid or expired refresh token')
    
    def test_token_refresh_without_token(self):
        """Test token refresh without providing refresh token"""
        response = self.client.post(self.refresh_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Refresh token is required')
    
    def test_rate_limiting_verification_codes(self):
        """Test rate limiting for verification code requests"""
        # Create user
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Mock send_verification_email to always succeed
        with patch('accounts.utils.send_verification_email', return_value=True):
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            # Send 3 verification codes (should succeed)
            for i in range(3):
                response = self.client.get(self.send_code_url)
                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            
            # 4th attempt should be rate limited
            response = self.client.get(self.send_code_url)
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            self.assertEqual(response.data['message'], 'Try again after 15 minutes')
    
    def test_verification_code_expiry(self):
        """Test verification code expiry after 15 minutes"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create user with old verification code
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        user.verification_code = 123456
        user.code_updated_at = timezone.now() - timedelta(minutes=20)  # 20 minutes ago
        user.save()
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Try to verify with expired code
        verify_data = {'verification_code': '123456'}
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.verify_url, verify_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(response.data['message'], 'Verification Code has expired')


class UserModelTestCase(TestCase):
    """Test User model functionality"""
    
    def test_user_creation(self):
        """Test user creation with all required fields"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertFalse(user.is_verified)
        self.assertEqual(user.status, 'pending_verification')
        self.assertFalse(user.has_paid)
    
    def test_user_str_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        
        self.assertEqual(str(user), 'test@example.com')
    
    def test_user_verification_fields(self):
        """Test user verification related fields"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            national_code='1234567890',
            phone_number='09123456789',
            gender='M',
            city='Tehran',
            university='Test University',
            major='Computer Science'
        )
        
        # Test initial state
        self.assertFalse(user.is_verified)
        self.assertEqual(user.status, 'pending_verification')
        self.assertIsNone(user.email_verified_at)
        self.assertEqual(user.try_count, 0)
        
        # Test verification
        user.is_verified = True
        user.status = 'verified'
        user.save()
        
        self.assertTrue(user.is_verified)
        self.assertEqual(user.status, 'verified')