const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static("public"));

// In-memory storage for demo (in production, use a database)
let users = new Map();
let wallets = new Map();
let transactions = [];

// Point exchange rate
const POINTS_PER_RUPEE = 10; // 10 points = ₹1

// Helper function to hash passwords (simple demo implementation)
function hashPassword(password) {
    // In production, use bcrypt or similar
    return Buffer.from(password).toString('base64');
}

// Helper function to verify passwords
function verifyPassword(password, hashedPassword) {
    return hashPassword(password) === hashedPassword;
}

// Register new user
app.post("/api/users/register", (req, res) => {
    const { name, email, password } = req.body;
    
    if (!name || !email || !password) {
        return res.status(400).json({ error: "Name, email, and password are required" });
    }

    // Check if user already exists
    for (const [id, user] of users) {
        if (user.email === email) {
            return res.status(409).json({ error: "User with this email already exists" });
        }
    }

    // Create new user
    const userId = 'USER_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    const newUser = {
        id: userId,
        name: name,
        email: email,
        password: hashPassword(password),
        createdAt: new Date().toISOString()
    };

    users.set(userId, newUser);

    // Initialize wallet
    wallets.set(userId, {
        userId: userId,
        balance: 0,
        totalEarned: 0,
        totalRedeemed: 0,
        history: []
    });

    // Return user without password
    const { password: _, ...userWithoutPassword } = newUser;

    res.json({
        success: true,
        user: userWithoutPassword,
        message: "User registered successfully"
    });
});

// Login user
app.post("/api/users/login", (req, res) => {
    const { email, password } = req.body;
    
    if (!email || !password) {
        return res.status(400).json({ error: "Email and password are required" });
    }

    // Find user by email
    let user = null;
    for (const [id, existingUser] of users) {
        if (existingUser.email === email) {
            user = existingUser;
            break;
        }
    }

    if (!user) {
        return res.status(404).json({ error: "User not found" });
    }

    // Verify password
    if (!verifyPassword(password, user.password)) {
        return res.status(401).json({ error: "Invalid password" });
    }

    // Return user without password
    const { password: _, ...userWithoutPassword } = user;

    res.json({
        success: true,
        user: userWithoutPassword,
        message: "Login successful"
    });
});

// Get user by ID
app.get("/api/users/:userId", (req, res) => {
    const userId = req.params.userId;
    const user = users.get(userId);
    const wallet = wallets.get(userId);
    
    if (!user) {
        return res.status(404).json({ error: "User not found" });
    }

    res.json({
        success: true,
        user: user,
        wallet: wallet || { balance: 0, totalEarned: 0, totalRedeemed: 0, history: [] }
    });
});

// Scan QR code and claim points
app.post("/api/scan-qr", async (req, res) => {
    try {
        const { qrData, userId } = req.body;
        
        if (!qrData || !userId) {
            return res.status(400).json({ 
                error: "QR data and user ID are required" 
            });
        }

        // Parse QR data
        let transactionData;
        try {
            // Try to parse as JSON first (for backward compatibility)
            if (qrData.startsWith('{')) {
                transactionData = JSON.parse(qrData);
            } else {
                // Parse the new string format: TRANSACTION:id|TYPE:type|WEIGHT:weight|POINTS:points|TIME:timestamp
                const parts = qrData.split('|');
                transactionData = {};
                
                parts.forEach(part => {
                    const [key, value] = part.split(':');
                    if (key && value) {
                        switch(key) {
                            case 'TRANSACTION':
                                transactionData.transactionId = value;
                                break;
                            case 'TYPE':
                                transactionData.wasteType = value;
                                break;
                            case 'WEIGHT':
                                transactionData.weight = parseFloat(value);
                                break;
                            case 'POINTS':
                                transactionData.points = parseInt(value);
                                break;
                            case 'TIME':
                                transactionData.timestamp = value;
                                break;
                        }
                    }
                });
            }
        } catch (e) {
            return res.status(400).json({ error: "Invalid QR code data format" });
        }

        // Validate transaction data
        if (!transactionData.transactionId || !transactionData.points || !transactionData.wasteType) {
            return res.status(400).json({ error: "Invalid transaction data in QR code" });
        }

        // Check if transaction already claimed
        const existingClaim = transactions.find(t => 
            t.transactionId === transactionData.transactionId
        );

        if (existingClaim) {
            return res.status(409).json({ 
                error: "Transaction already claimed",
                claimedBy: existingClaim.userId
            });
        }

        // For anonymous transactions, we'll use the provided userId from the request
        // This allows users to claim points to their own wallet
        const user = users.get(userId);
        if (!user) {
            return res.status(404).json({ error: "User not found. Please login first." });
        }

        // Get user wallet
        let wallet = wallets.get(user.id);
        if (!wallet) {
            // Create wallet if it doesn't exist (safety check)
            wallet = {
                userId: user.id,
                balance: 0,
                totalEarned: 0,
                totalRedeemed: 0,
                history: []
            };
            wallets.set(user.id, wallet);
        }

        // Add points to wallet
        const points = parseInt(transactionData.points);
        wallet.balance += points;
        wallet.totalEarned += points;

        // Record transaction
        const claimTransaction = {
            id: 'CLAIM_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
            userId: user.id,
            transactionId: transactionData.transactionId,
            points: points,
            wasteType: transactionData.wasteType,
            weight: transactionData.weight,
            timestamp: new Date().toISOString(),
            type: 'claim'
        };

        transactions.push(claimTransaction);

        // Add to wallet history
        wallet.history.unshift({
            id: claimTransaction.id,
            type: 'earned',
            points: points,
            wasteType: transactionData.wasteType,
            weight: transactionData.weight,
            timestamp: claimTransaction.timestamp,
            description: `Earned ${points} points from ${transactionData.wasteType} waste`
        });

        res.json({
            success: true,
            message: `Successfully claimed ${points} points for ${user.name}!`,
            transaction: claimTransaction,
            wallet: wallet,
            user: user
        });

    } catch (error) {
        console.error("Error scanning QR:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

// Get wallet balance
app.get("/api/wallet/:userId", (req, res) => {
    const userId = req.params.userId;
    let wallet = wallets.get(userId);
    
    if (!wallet) {
        // Create wallet if it doesn't exist
        wallet = {
            userId: userId,
            balance: 0,
            totalEarned: 0,
            totalRedeemed: 0,
            history: []
        };
        wallets.set(userId, wallet);
    }

    res.json({
        success: true,
        wallet: wallet
    });
});

// Redeem points for money
app.post("/api/wallet/:userId/redeem", (req, res) => {
    const userId = req.params.userId;
    const { amountRupees } = req.body;
    
    if (!amountRupees || amountRupees <= 0) {
        return res.status(400).json({ error: "Invalid amount" });
    }

    let wallet = wallets.get(userId);
    if (!wallet) {
        // Create wallet if it doesn't exist
        wallet = {
            userId: userId,
            balance: 0,
            totalEarned: 0,
            totalRedeemed: 0,
            history: []
        };
        wallets.set(userId, wallet);
    }

    const pointsNeeded = Math.ceil(amountRupees * POINTS_PER_RUPEE);
    
    if (wallet.balance < pointsNeeded) {
        return res.status(400).json({ 
            error: "Insufficient points",
            currentBalance: wallet.balance,
            pointsNeeded: pointsNeeded,
            amountRequested: amountRupees
        });
    }

    // Deduct points
    wallet.balance -= pointsNeeded;
    wallet.totalRedeemed += pointsNeeded;

    // Record redemption transaction
    const redemptionTransaction = {
        id: 'REDEEM_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
        userId: userId,
        points: -pointsNeeded,
        amountRupees: amountRupees,
        timestamp: new Date().toISOString(),
        type: 'redemption'
    };

    transactions.push(redemptionTransaction);

    // Add to wallet history
    wallet.history.unshift({
        id: redemptionTransaction.id,
        type: 'redeemed',
        points: -pointsNeeded,
        amountRupees: amountRupees,
        timestamp: redemptionTransaction.timestamp,
        description: `Redeemed ₹${amountRupees} for ${pointsNeeded} points`
    });

    res.json({
        success: true,
        message: `Successfully redeemed ₹${amountRupees}`,
        transaction: redemptionTransaction,
        wallet: wallet,
        exchangeRate: `₹1 = ${POINTS_PER_RUPEE} points`
    });
});

// Get user transaction history
app.get("/api/transactions/:userId", (req, res) => {
    const userId = req.params.userId;
    const userTransactions = transactions.filter(t => t.userId === userId);
    
    res.json({
        success: true,
        transactions: userTransactions,
        total: userTransactions.length
    });
});

// Get all users (for admin purposes)
app.get("/api/users", (req, res) => {
    const usersList = Array.from(users.values()).map(user => {
        const wallet = wallets.get(user.id);
        return {
            ...user,
            wallet: wallet || { balance: 0, totalEarned: 0, totalRedeemed: 0 }
        };
    });

    res.json({
        success: true,
        users: usersList,
        total: usersList.length
    });
});

// Get system statistics
app.get("/api/stats", (req, res) => {
    const totalUsers = users.size;
    const totalPoints = Array.from(wallets.values()).reduce((sum, w) => sum + w.balance, 0);
    const totalEarned = Array.from(wallets.values()).reduce((sum, w) => sum + w.totalEarned, 0);
    const totalRedeemed = Array.from(wallets.values()).reduce((sum, w) => sum + w.totalRedeemed, 0);
    const totalTransactions = transactions.length;

    res.json({
        success: true,
        stats: {
            totalUsers,
            totalPoints,
            totalEarned,
            totalRedeemed,
            totalTransactions,
            totalMoneyRedeemed: (totalRedeemed / POINTS_PER_RUPEE).toFixed(2)
        }
    });
});

// Create demo user for testing
app.post("/api/demo-user", (req, res) => {
    try {
        const demoEmail = 'demo@example.com';
        const demoPassword = 'demo123';
        const demoName = 'Demo User';

        // Check if demo user already exists
        for (const [id, user] of users) {
            if (user.email === demoEmail) {
                const { password: _, ...userWithoutPassword } = user;
                return res.json({
                    success: true,
                    user: userWithoutPassword,
                    message: "Demo user already exists"
                });
            }
        }

        // Create demo user
        const userId = 'DEMO_USER_' + Date.now();
        const demoUser = {
            id: userId,
            name: demoName,
            email: demoEmail,
            password: hashPassword(demoPassword),
            createdAt: new Date().toISOString()
        };

        users.set(userId, demoUser);

        // Initialize wallet with some demo points
        wallets.set(userId, {
            userId: userId,
            balance: 50, // Start with 50 points
            totalEarned: 50,
            totalRedeemed: 0,
            history: [{
                id: 'DEMO_POINTS',
                type: 'earned',
                points: 50,
                timestamp: new Date().toISOString(),
                description: 'Demo points for testing'
            }]
        });

        // Return user without password
        const { password: _, ...userWithoutPassword } = demoUser;

        res.json({
            success: true,
            user: userWithoutPassword,
            message: "Demo user created successfully with 50 points",
            credentials: {
                email: demoEmail,
                password: demoPassword
            }
        });
    } catch (error) {
        console.error("Error creating demo user:", error);
        res.status(500).json({ error: "Failed to create demo user" });
    }
});

const PORT = process.env.PORT || 3002;
app.listen(PORT, () => {
    console.log(`👤 User App Server running on http://localhost:${PORT}`);
    console.log(`💳 Wallet management available at http://localhost:${PORT}/wallet.html`);
});
