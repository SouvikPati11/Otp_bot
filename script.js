// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();

// Global variables
let currentOrder = null;
let otpCheckInterval = null;
let refundTimeout = null;

// DOM Elements
const buyForm = document.getElementById('buyForm');
const otpCard = document.getElementById('otpCard');
const phoneNumberEl = document.getElementById('phoneNumber');
const otpCodeEl = document.getElementById('otpCode');
const refreshOtpBtn = document.getElementById('refreshOtp');
const cancelOrderBtn = document.getElementById('cancelOrder');
const userBalanceEl = document.getElementById('userBalance');
const historyTable = document.getElementById('historyTable');

// Initialize the app
document.addEventListener('DOMContentLoaded', async () => {
    // Set up event listeners
    buyForm.addEventListener('submit', handleBuyNumber);
    refreshOtpBtn.addEventListener('click', checkOTP);
    cancelOrderBtn.addEventListener('click', cancelOrder);
    
    // Load user data
    await loadUserData();
    
    // If we have an active order, show OTP card
    if (localStorage.getItem('currentOrder')) {
        currentOrder = JSON.parse(localStorage.getItem('currentOrder'));
        showOTPCard(currentOrder);
        startOTPCheck();
    }
});

async function loadUserData() {
    try {
        // In a real app, you would fetch this from your backend
        const response = await fetch('/api/user/balance');
        const data = await response.json();
        
        userBalanceEl.textContent = `${data.balance} ${data.currency || 'USD'}`;
        
        // Load history
        const historyResponse = await fetch('/api/user/history');
        const historyData = await historyResponse.json();
        
        renderHistory(historyData);
    } catch (error) {
        console.error('Error loading user data:', error);
        userBalanceEl.textContent = 'Error loading balance';
    }
}

function renderHistory(history) {
    if (history.length === 0) {
        historyTable.innerHTML = '<tr><td colspan="4" class="text-center">No purchases yet</td></tr>';
        return;
    }
    
    const rows = history.map(item => `
        <tr>
            <td>${new Date(item.date).toLocaleString()}</td>
            <td>${item.service}</td>
            <td>${item.number}</td>
            <td><span class="badge ${item.status === 'success' ? 'bg-success' : 'bg-warning'}">${item.status}</span></td>
        </tr>
    `).join('');
    
    historyTable.innerHTML = rows;
}

async function handleBuyNumber(e) {
    e.preventDefault();
    
    const country = document.getElementById('country').value;
    const service = document.getElementById('service').value;
    
    const buyBtn = document.getElementById('buyBtn');
    const spinner = document.getElementById('spinner');
    
    buyBtn.disabled = true;
    spinner.classList.remove('d-none');
    
    try {
        // Call backend to purchase number
        const response = await fetch('/api/buy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ country, service })
        });
        
        const data = await response.json();
        
        if (data.error) {
            tg.showPopup({ title: 'Error', message: data.error });
            return;
        }
        
        currentOrder = data;
        localStorage.setItem('currentOrder', JSON.stringify(currentOrder));
        
        showOTPCard(data);
        startOTPCheck();
        
        // Update balance
        await loadUserData();
    } catch (error) {
        console.error('Error buying number:', error);
        tg.showPopup({ title: 'Error', message: 'Failed to purchase number. Please try again.' });
    } finally {
        buyBtn.disabled = false;
        spinner.classList.add('d-none');
    }
}

function showOTPCard(order) {
    phoneNumberEl.textContent = order.phone;
    otpCodeEl.textContent = 'Waiting...';
    otpCard.classList.remove('d-none');
}

function startOTPCheck() {
    // Clear any existing interval
    if (otpCheckInterval) clearInterval(otpCheckInterval);
    
    // Check immediately
    checkOTP();
    
    // Then check every 10 seconds
    otpCheckInterval = setInterval(checkOTP, 10000);
    
    // Set up refund timeout (15 minutes)
    if (refundTimeout) clearTimeout(refundTimeout);
    refundTimeout = setTimeout(() => {
        if (otpCodeEl.textContent === 'Waiting...') {
            tg.showPopup({ 
                title: 'Timeout', 
                message: 'No OTP received within 15 minutes. Your balance has been refunded.'
            });
            clearOrder();
        }
    }, 15 * 60 * 1000);
}

async function checkOTP() {
    if (!currentOrder) return;
    
    try {
        const response = await fetch(`/api/check/${currentOrder.orderId}`);
        const data = await response.json();
        
        if (data.otp) {
            otpCodeEl.textContent = data.otp;
            clearInterval(otpCheckInterval);
            clearTimeout(refundTimeout);
            
            // Add slight delay before clearing to let user see the OTP
            setTimeout(() => {
                tg.showPopup({ 
                    title: 'Success', 
                    message: `OTP received: ${data.otp}`
                });
                clearOrder();
            }, 2000);
        }
    } catch (error) {
        console.error('Error checking OTP:', error);
    }
}

async function cancelOrder() {
    if (!currentOrder) return;
    
    try {
        const response = await fetch(`/api/cancel/${currentOrder.orderId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            tg.showPopup({ 
                title: 'Cancelled', 
                message: 'Order cancelled and balance refunded.'
            });
            clearOrder();
            await loadUserData();
        }
    } catch (error) {
        console.error('Error cancelling order:', error);
        tg.showPopup({ 
            title: 'Error', 
            message: 'Failed to cancel order. Please try again.'
        });
    }
}

function clearOrder() {
    clearInterval(otpCheckInterval);
    clearTimeout(refundTimeout);
    localStorage.removeItem('currentOrder');
    currentOrder = null;
    otpCard.classList.add('d-none');
}
