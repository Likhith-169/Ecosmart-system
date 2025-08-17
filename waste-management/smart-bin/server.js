const express = require("express");
const bodyParser = require("body-parser");
const QRCode = require("qrcode");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static("public"));

// In-memory storage for demo (in production, use a database)
let transactions = [];
let users = new Map();

// Point multipliers for different waste types
const wasteMultipliers = {
    plastic: 5,
    metal: 10,
    organic: 2,
    paper: 3,
    glass: 7,
    electronic: 15
};

// Generate unique transaction ID
function generateTransactionId() {
    return 'TXN_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Calculate points based on waste type and weight
function calculatePoints(wasteType, weight) {
    const multiplier = wasteMultipliers[wasteType] || 1;
    return Math.floor(weight * multiplier);
}

// Smart Bin: Submit waste and generate QR code
app.post("/api/dispose-waste", async (req, res) => {
    try {
        const { wasteType, weight } = req.body;
        
        if (!wasteType || !weight) {
            return res.status(400).json({ 
                error: "Waste type and weight are required" 
            });
        }

        // Validate waste type
        if (!wasteMultipliers[wasteType]) {
            return res.status(400).json({ 
                error: "Invalid waste type. Allowed types: " + Object.keys(wasteMultipliers).join(", ")
            });
        }

        // Validate weight
        if (weight <= 0) {
            return res.status(400).json({ error: "Weight must be greater than 0" });
        }

        // Calculate points
        const points = Math.round(weight * wasteMultipliers[wasteType]);
        const timestamp = new Date().toISOString();
        const transactionId = 'TXN_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

        // Create transaction record
        const transaction = {
            id: transactionId,
            wasteType: wasteType,
            weight: parseFloat(weight),
            points: points,
            timestamp: timestamp,
            status: 'pending' // pending, claimed, expired
        };

        // Store transaction
        transactions.push(transaction);

        // Generate QR code with transaction data
        const qrData = {
            transactionId: transactionId,
            wasteType: wasteType,
            weight: weight,
            points: points,
            timestamp: timestamp
        };

        // Create a simple string format for easier scanning
        const qrString = `TRANSACTION:${transactionId}|TYPE:${wasteType}|WEIGHT:${weight}|POINTS:${points}|TIME:${timestamp}`;
        
        const qrCode = await QRCode.toDataURL(qrString);

        res.json({
            success: true,
            transaction: transaction,
            qrCode: qrCode,
            qrData: qrString, // Also send the string data for easy copying
            message: `Waste disposed successfully! Earned ${points} points.`
        });

    } catch (error) {
        console.error("Error disposing waste:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

// Get all transactions (for real-time monitoring)
app.get("/api/transactions", (req, res) => {
    res.json({
        success: true,
        transactions: transactions,
        total: transactions.length
    });
});

// Get transactions by user
app.get("/api/transactions/user/:userId", (req, res) => {
    const userId = req.params.userId;
    const userTransactions = transactions.filter(t => t.userId === userId);
    
    res.json({
        success: true,
        transactions: userTransactions,
        total: userTransactions.length
    });
});

// Get real-time waste flow data
app.get("/api/waste-flow", (req, res) => {
    const flowData = {};
    
    // Group by waste type
    transactions.forEach(t => {
        if (!flowData[t.wasteType]) {
            flowData[t.wasteType] = {
                count: 0,
                totalWeight: 0,
                totalPoints: 0
            };
        }
        flowData[t.wasteType].count++;
        flowData[t.wasteType].totalWeight += t.weight;
        flowData[t.wasteType].totalPoints += t.points;
    });

    res.json({
        success: true,
        flowData: flowData,
        summary: {
            totalTransactions: transactions.length,
            totalWasteDisposed: transactions.reduce((sum, t) => sum + t.weight, 0),
            totalPointsGenerated: transactions.reduce((sum, t) => sum + t.points, 0)
        }
    });
});

// Create or get user
app.post("/api/users", (req, res) => {
    const { name, email } = req.body;
    
    if (!name || !email) {
        return res.status(400).json({ error: "Name and email are required" });
    }

    // Check if user exists
    for (const [id, user] of users) {
        if (user.email === email) {
            return res.json({ success: true, user: user });
        }
    }

    // Create new user
    const userId = 'USER_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    const newUser = {
        id: userId,
        name: name,
        email: email,
        createdAt: new Date().toISOString(),
        totalPoints: 0,
        totalWasteDisposed: 0
    };

    users.set(userId, newUser);

    res.json({
        success: true,
        user: newUser,
        message: "User created successfully"
    });
});

// Get user by ID
app.get("/api/users/:userId", (req, res) => {
    const userId = req.params.userId;
    const user = users.get(userId);
    
    if (!user) {
        return res.status(404).json({ error: "User not found" });
    }

    // Calculate user statistics
    const userTransactions = transactions.filter(t => t.userId === userId);
    user.totalPoints = userTransactions.reduce((sum, t) => sum + t.points, 0);
    user.totalWasteDisposed = userTransactions.reduce((sum, t) => sum + t.weight, 0);
    user.transactionCount = userTransactions.length;

    res.json({
        success: true,
        user: user
    });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
    console.log(`🗑️ Smart Bin Server running on http://localhost:${PORT}`);
    console.log(`📊 Real-time monitoring available at http://localhost:${PORT}/monitor.html`);
});
