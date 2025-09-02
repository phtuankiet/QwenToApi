local imageUrl = "https://files.catbox.moe/kqq444.jpg"
local chat = {
    "m nqu ma",
    "cn choa",
    "th nghèo",
    "sua em",
    "le em",
    "manh e",
    "tk nqu",
    "cay ak",
    "tk nqu ei",
    "m nqu ma e",
    "tk oc kac",
    "cay bo ak"
}

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local VirtualUser = game:GetService("VirtualUser")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local camera = Workspace.CurrentCamera

local isRunning = false
local isDragging = false
local dragStart = nil
local startPos = nil
local menuOpen = false
local espEnabled = false
local espElements = {}
local autoAttackEnabled = false
local autoAttackGUIVisible = false
local spinAroundEnabled = false
local spinAroundConnection = nil
local autoAttackConnection = nil
local autoFarmEnabled = false
local autoFarmGUIVisible = false
local lastPosition = nil
local lastPositionTime = tick()
local teleportCooldown = 3
local autoJumpEnabled = false
local autoJumpGUIVisible = false
local autoJumpConnection = nil
local debugEnabled = false
local debugConnection = nil
local debugLabel = nil
local maxTeleportDistance = 20
local autoFarmConnection = nil
local currentTargetNPC = nil
local farmDistance = 4
local chatWarEnabled = false
local chatWarGUIVisible = false
local chatWarConnection = nil
local speedHackEnabled = false
local speedHackGUIVisible = false
local speedHackConnection = nil
local customSpeed = 3.0
local originalWalkSpeed = 16
local aimbotEnabled = false
local aimbotGUIVisible = false
local selectedTarget = nil
local aimbotConnection = nil
local fovCircle = nil
local fovSize = 100
local aimbotDropdownOpen = false
local playersList = {}

player.Idled:Connect(function()
    VirtualUser:CaptureController()
    VirtualUser:ClickButton2(Vector2.new())
end)

wait(1)

if playerGui:FindFirstChild("ChatWarGUI") then
    playerGui.ChatWarGUI:Destroy()
end

local screenGui = Instance.new("ScreenGui")
screenGui.Name = "ChatWarGUI"
screenGui.ResetOnSpawn = false
screenGui.Parent = playerGui

local logoButton = Instance.new("ImageButton")
logoButton.Name = "LogoButton"
logoButton.Parent = screenGui
logoButton.Size = UDim2.new(0, 55, 0, 55)
logoButton.Position = UDim2.new(0, 20, 0, 100)
logoButton.BackgroundColor3 = Color3.fromRGB(25, 25, 25)
logoButton.BorderSizePixel = 0
logoButton.Image = "rbxassetid://84370538595330"
logoButton.ScaleType = Enum.ScaleType.Crop
logoButton.ZIndex = 10
logoButton.Active = true
logoButton.Draggable = false

local logoCorner = Instance.new("UICorner")
logoCorner.CornerRadius = UDim.new(1, 0)
logoCorner.Parent = logoButton

local logoStroke = Instance.new("UIStroke")
logoStroke.Color = Color3.fromRGB(0, 200, 255)
logoStroke.Thickness = 2
logoStroke.Parent = logoButton

local mainFrame = Instance.new("Frame")
mainFrame.Name = "MainFrame"
mainFrame.Parent = screenGui
mainFrame.Size = UDim2.new(0, 340, 0, 285)
mainFrame.Position = UDim2.new(0.5, -160, 0.5, -125)
mainFrame.BackgroundColor3 = Color3.fromRGB(18, 18, 20)
mainFrame.BorderSizePixel = 0
mainFrame.Visible = false
mainFrame.ZIndex = 5
mainFrame.Active = true
mainFrame.Draggable = false

local mainCorner = Instance.new("UICorner")
mainCorner.CornerRadius = UDim.new(0, 20)
mainCorner.Parent = mainFrame

local mainStroke = Instance.new("UIStroke")
mainStroke.Color = Color3.fromRGB(0, 200, 255)
mainStroke.Thickness = 2
mainStroke.Parent = mainFrame

local mainGradient = Instance.new("UIGradient")
mainGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(18, 18, 20)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(25, 25, 30))
}
mainGradient.Rotation = 45
mainGradient.Parent = mainFrame

local titleLabel = Instance.new("TextLabel")
titleLabel.Name = "TitleLabel"
titleLabel.Parent = mainFrame
titleLabel.Size = UDim2.new(1, -50, 0, 35)
titleLabel.Position = UDim2.new(0, 15, 0, 5)
titleLabel.BackgroundTransparency = 1
titleLabel.Text = "Pham Tuan Kiet"
titleLabel.TextColor3 = Color3.fromRGB(0, 200, 255)
titleLabel.TextSize = 20
titleLabel.TextXAlignment = Enum.TextXAlignment.Left
titleLabel.Font = Enum.Font.GothamBold
titleLabel.ZIndex = 6

local closeButton = Instance.new("TextButton")
closeButton.Name = "CloseButton"
closeButton.Parent = mainFrame
closeButton.Size = UDim2.new(0, 30, 0, 30)
closeButton.Position = UDim2.new(1, -35, 0, 5)
closeButton.BackgroundColor3 = Color3.fromRGB(255, 60, 60)
closeButton.BorderSizePixel = 0
closeButton.Text = "X"
closeButton.TextColor3 = Color3.fromRGB(255, 255, 255)
closeButton.TextSize = 16
closeButton.Font = Enum.Font.GothamBold
closeButton.ZIndex = 6

local closeCorner = Instance.new("UICorner")
closeCorner.CornerRadius = UDim.new(1, 0)
closeCorner.Parent = closeButton

local espLabel = Instance.new("TextLabel")
espLabel.Name = "ESPLabel"
espLabel.Parent = mainFrame
espLabel.Size = UDim2.new(0, 50, 0, 25)
espLabel.Position = UDim2.new(0, 15, 0, 50)
espLabel.BackgroundTransparency = 1
espLabel.Text = "ESP:"
espLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
espLabel.TextSize = 14
espLabel.TextXAlignment = Enum.TextXAlignment.Left
espLabel.Font = Enum.Font.Gotham
espLabel.ZIndex = 6

local espToggle = Instance.new("TextButton")
espToggle.Name = "ESPToggle"
espToggle.Parent = mainFrame
espToggle.Size = UDim2.new(0, 50, 0, 30)
espToggle.Position = UDim2.new(0, 75, 0, 47)
espToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
espToggle.BorderSizePixel = 0
espToggle.Text = "OFF"
espToggle.TextColor3 = Color3.fromRGB(255, 255, 255)
espToggle.TextSize = 12
espToggle.Font = Enum.Font.GothamBold
espToggle.ZIndex = 6

local espToggleCorner = Instance.new("UICorner")
espToggleCorner.CornerRadius = UDim.new(0, 15)
espToggleCorner.Parent = espToggle

local espToggleGradient = Instance.new("UIGradient")
espToggleGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
}
espToggleGradient.Rotation = 90
espToggleGradient.Parent = espToggle

local autoAttackLabel = Instance.new("TextLabel")
autoAttackLabel.Name = "AutoAttackLabel"
autoAttackLabel.Parent = mainFrame
autoAttackLabel.Size = UDim2.new(0, 90, 0, 25)
autoAttackLabel.Position = UDim2.new(0, 15, 0, 85)
autoAttackLabel.BackgroundTransparency = 1
autoAttackLabel.Text = "Auto Attack:"
autoAttackLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
autoAttackLabel.TextSize = 14
autoAttackLabel.TextXAlignment = Enum.TextXAlignment.Left
autoAttackLabel.Font = Enum.Font.Gotham
autoAttackLabel.ZIndex = 6

local autoAttackToggle = Instance.new("TextButton")
autoAttackToggle.Name = "AutoAttackToggle"
autoAttackToggle.Parent = mainFrame
autoAttackToggle.Size = UDim2.new(0, 50, 0, 30)
autoAttackToggle.Position = UDim2.new(0, 115, 0, 82)
autoAttackToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
autoAttackToggle.BorderSizePixel = 0
autoAttackToggle.Text = "OFF"
autoAttackToggle.TextColor3 = Color3.fromRGB(255, 255, 255)
autoAttackToggle.TextSize = 12
autoAttackToggle.Font = Enum.Font.GothamBold
autoAttackToggle.ZIndex = 6

local autoAttackToggleCorner = Instance.new("UICorner")
autoAttackToggleCorner.CornerRadius = UDim.new(0, 15)
autoAttackToggleCorner.Parent = autoAttackToggle

local autoAttackToggleGradient = Instance.new("UIGradient")
autoAttackToggleGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
}
autoAttackToggleGradient.Rotation = 90
autoAttackToggleGradient.Parent = autoAttackToggle

local chatWarLabel = Instance.new("TextLabel")
chatWarLabel.Name = "ChatWarLabel"
chatWarLabel.Parent = mainFrame
chatWarLabel.Size = UDim2.new(0, 80, 0, 25)
chatWarLabel.Position = UDim2.new(0, 15, 0, 120)
chatWarLabel.BackgroundTransparency = 1
chatWarLabel.Text = "Chat War:"
chatWarLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
chatWarLabel.TextSize = 14
chatWarLabel.TextXAlignment = Enum.TextXAlignment.Left
chatWarLabel.Font = Enum.Font.Gotham
chatWarLabel.ZIndex = 6

local chatWarToggle = Instance.new("TextButton")
chatWarToggle.Name = "ChatWarToggle"
chatWarToggle.Parent = mainFrame
chatWarToggle.Size = UDim2.new(0, 50, 0, 30)
chatWarToggle.Position = UDim2.new(0, 105, 0, 117)
chatWarToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
chatWarToggle.BorderSizePixel = 0
chatWarToggle.Text = "OFF"
chatWarToggle.TextColor3 = Color3.fromRGB(255, 255, 255)
chatWarToggle.TextSize = 12
chatWarToggle.Font = Enum.Font.GothamBold
chatWarToggle.ZIndex = 6

local chatWarToggleCorner = Instance.new("UICorner")
chatWarToggleCorner.CornerRadius = UDim.new(0, 15)
chatWarToggleCorner.Parent = chatWarToggle

local chatWarToggleGradient = Instance.new("UIGradient")
chatWarToggleGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
}
chatWarToggleGradient.Rotation = 90
chatWarToggleGradient.Parent = chatWarToggle

local speedLabel = Instance.new("TextLabel")
speedLabel.Name = "SpeedLabel"
speedLabel.Parent = mainFrame
speedLabel.Size = UDim2.new(0, 80, 0, 25)
speedLabel.Position = UDim2.new(0, 15, 0, 155)
speedLabel.BackgroundTransparency = 1
speedLabel.Text = "Hack Speed:"
speedLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
speedLabel.TextSize = 14
speedLabel.TextXAlignment = Enum.TextXAlignment.Left
speedLabel.Font = Enum.Font.Gotham
speedLabel.ZIndex = 6

local speedToggle = Instance.new("TextButton")
speedToggle.Name = "SpeedToggle"
speedToggle.Parent = mainFrame
speedToggle.Size = UDim2.new(0, 50, 0, 30)
speedToggle.Position = UDim2.new(0, 105, 0, 152)
speedToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
speedToggle.BorderSizePixel = 0
speedToggle.Text = "OFF"
speedToggle.TextColor3 = Color3.fromRGB(255, 255, 255)
speedToggle.TextSize = 12
speedToggle.Font = Enum.Font.GothamBold
speedToggle.ZIndex = 6

local speedToggleCorner = Instance.new("UICorner")
speedToggleCorner.CornerRadius = UDim.new(0, 15)
speedToggleCorner.Parent = speedToggle

local speedToggleGradient = Instance.new("UIGradient")
speedToggleGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
}
speedToggleGradient.Rotation = 90
speedToggleGradient.Parent = speedToggle

local jumpLabel = Instance.new("TextLabel")
jumpLabel.Name = "JumpLabel"
jumpLabel.Parent = mainFrame
jumpLabel.Size = UDim2.new(0, 80, 0, 25)
jumpLabel.Position = UDim2.new(0, 175, 0, 155)
jumpLabel.BackgroundTransparency = 1
jumpLabel.Text = "Auto Jump:"
jumpLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
jumpLabel.TextSize = 14
jumpLabel.TextXAlignment = Enum.TextXAlignment.Left
jumpLabel.Font = Enum.Font.Gotham
jumpLabel.ZIndex = 6

local jumpToggle = Instance.new("TextButton")
jumpToggle.Name = "JumpToggle"
jumpToggle.Parent = mainFrame
jumpToggle.Size = UDim2.new(0, 50, 0, 30)
jumpToggle.Position = UDim2.new(0, 265, 0, 152)
jumpToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
jumpToggle.BorderSizePixel = 0
jumpToggle.Text = "OFF"
jumpToggle.TextColor3 = Color3.fromRGB(255, 255, 255)
jumpToggle.TextSize = 12
jumpToggle.Font = Enum.Font.GothamBold
jumpToggle.ZIndex = 6

local jumpToggleCorner = Instance.new("UICorner")
jumpToggleCorner.CornerRadius = UDim.new(0, 15)
jumpToggleCorner.Parent = jumpToggle

local jumpToggleGradient = Instance.new("UIGradient")
jumpToggleGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
}
jumpToggleGradient.Rotation = 90
jumpToggleGradient.Parent = jumpToggle

local autoFarmLabel = Instance.new("TextLabel")
autoFarmLabel.Name = "AutoFarmLabel"
autoFarmLabel.Parent = mainFrame
autoFarmLabel.Size = UDim2.new(0, 90, 0, 25)
autoFarmLabel.Position = UDim2.new(0, 15, 0, 190)
autoFarmLabel.BackgroundTransparency = 1
autoFarmLabel.Text = "Auto Farm:"
autoFarmLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
autoFarmLabel.TextSize = 14
autoFarmLabel.TextXAlignment = Enum.TextXAlignment.Left
autoFarmLabel.Font = Enum.Font.Gotham
autoFarmLabel.ZIndex = 6

local autoFarmToggle = Instance.new("TextButton")
autoFarmToggle.Name = "AutoFarmToggle"
autoFarmToggle.Parent = mainFrame
autoFarmToggle.Size = UDim2.new(0, 50, 0, 30)
autoFarmToggle.Position = UDim2.new(0, 115, 0, 187)
autoFarmToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
autoFarmToggle.BorderSizePixel = 0
autoFarmToggle.Text = "OFF"
autoFarmToggle.TextColor3 = Color3.fromRGB(255, 255, 255)
autoFarmToggle.TextSize = 12
autoFarmToggle.Font = Enum.Font.GothamBold
autoFarmToggle.ZIndex = 6

local autoFarmToggleCorner = Instance.new("UICorner")
autoFarmToggleCorner.CornerRadius = UDim.new(0, 15)
autoFarmToggleCorner.Parent = autoFarmToggle

local autoFarmToggleGradient = Instance.new("UIGradient")
autoFarmToggleGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
}
autoFarmToggleGradient.Rotation = 90
autoFarmToggleGradient.Parent = autoFarmToggle

local autoHealLabel = Instance.new("TextLabel")
autoHealLabel.Name = "AutoHealLabel"
autoHealLabel.Parent = mainFrame
autoHealLabel.Size = UDim2.new(0, 80, 0, 25)
autoHealLabel.Position = UDim2.new(0, 175, 0, 85)
autoHealLabel.BackgroundTransparency = 1
autoHealLabel.Text = "Quay Tròn:"
autoHealLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
autoHealLabel.TextSize = 14
autoHealLabel.TextXAlignment = Enum.TextXAlignment.Left
autoHealLabel.Font = Enum.Font.Gotham
autoHealLabel.ZIndex = 6

local autoHealToggle = Instance.new("TextButton")
autoHealToggle.Name = "AutoHealToggle"
autoHealToggle.Parent = mainFrame
autoHealToggle.Size = UDim2.new(0, 50, 0, 30)
autoHealToggle.Position = UDim2.new(0, 265, 0, 82)
autoHealToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
autoHealToggle.BorderSizePixel = 0
autoHealToggle.Text = "OFF"
autoHealToggle.TextColor3 = Color3.fromRGB(255, 255, 255)
autoHealToggle.TextSize = 12
autoHealToggle.Font = Enum.Font.GothamBold
autoHealToggle.ZIndex = 6

local autoHealToggleCorner = Instance.new("UICorner")
autoHealToggleCorner.CornerRadius = UDim.new(0, 15)
autoHealToggleCorner.Parent = autoHealToggle

local autoHealToggleGradient = Instance.new("UIGradient")
autoHealToggleGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
}
autoHealToggleGradient.Rotation = 90
autoHealToggleGradient.Parent = autoHealToggle
 
local debugLabel = Instance.new("TextLabel")
debugLabel.Name = "DebugLabel"
debugLabel.Parent = mainFrame
debugLabel.Size = UDim2.new(0, 80, 0, 25)
debugLabel.Position = UDim2.new(0, 175, 0, 120)
debugLabel.BackgroundTransparency = 1
debugLabel.Text = "Debug UI:"
debugLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
debugLabel.TextSize = 14
debugLabel.TextXAlignment = Enum.TextXAlignment.Left
debugLabel.Font = Enum.Font.Gotham
debugLabel.ZIndex = 6

local debugToggle = Instance.new("TextButton")
debugToggle.Name = "DebugToggle"
debugToggle.Parent = mainFrame
debugToggle.Size = UDim2.new(0, 50, 0, 30)
debugToggle.Position = UDim2.new(0, 265, 0, 117)
debugToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
debugToggle.BorderSizePixel = 0
debugToggle.Text = "OFF"
debugToggle.TextColor3 = Color3.fromRGB(255, 255, 255)
debugToggle.TextSize = 12
debugToggle.Font = Enum.Font.GothamBold
debugToggle.ZIndex = 6

local aimbotLabel = Instance.new("TextLabel")
aimbotLabel.Name = "AimbotLabel"
aimbotLabel.Parent = mainFrame
aimbotLabel.Size = UDim2.new(0, 80, 0, 25)
aimbotLabel.Position = UDim2.new(0, 175, 0, 190)
aimbotLabel.BackgroundTransparency = 1
aimbotLabel.Text = "Aimbot:"
aimbotLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
aimbotLabel.TextSize = 14
aimbotLabel.TextXAlignment = Enum.TextXAlignment.Left
aimbotLabel.Font = Enum.Font.Gotham
aimbotLabel.ZIndex = 6

local aimbotToggle = Instance.new("TextButton")
aimbotToggle.Name = "AimbotToggle"
aimbotToggle.Parent = mainFrame
aimbotToggle.Size = UDim2.new(0, 50, 0, 30)
aimbotToggle.Position = UDim2.new(0, 265, 0, 187)
aimbotToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
aimbotToggle.BorderSizePixel = 0
aimbotToggle.Text = "OFF"
aimbotToggle.TextColor3 = Color3.fromRGB(255, 255, 255)
aimbotToggle.TextSize = 12
aimbotToggle.Font = Enum.Font.GothamBold
aimbotToggle.ZIndex = 6

local aimbotToggleCorner = Instance.new("UICorner")
aimbotToggleCorner.CornerRadius = UDim.new(0, 15)
aimbotToggleCorner.Parent = aimbotToggle

local aimbotToggleGradient = Instance.new("UIGradient")
aimbotToggleGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
}
aimbotToggleGradient.Rotation = 90
aimbotToggleGradient.Parent = aimbotToggle

local debugToggleCorner = Instance.new("UICorner")
debugToggleCorner.CornerRadius = UDim.new(0, 15)
debugToggleCorner.Parent = debugToggle

local debugToggleGradient = Instance.new("UIGradient")
debugToggleGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
}
debugToggleGradient.Rotation = 90
debugToggleGradient.Parent = debugToggle

local statusLabel = Instance.new("TextLabel")
statusLabel.Name = "StatusLabel"
statusLabel.Parent = mainFrame
statusLabel.Size = UDim2.new(1, -30, 0, 60)
statusLabel.Position = UDim2.new(0, 15, 0, 225)
statusLabel.BackgroundTransparency = 1
statusLabel.Text = "Ready To Use"
statusLabel.TextColor3 = Color3.fromRGB(0, 200, 255)
statusLabel.TextSize = 12
statusLabel.TextWrapped = true
statusLabel.Font = Enum.Font.Gotham
statusLabel.TextYAlignment = Enum.TextYAlignment.Top
statusLabel.ZIndex = 6

local debugDisplay = Instance.new("Frame")
debugDisplay.Name = "DebugDisplay"
debugDisplay.Parent = screenGui
debugDisplay.Size = UDim2.new(0, 350, 0, 400)
debugDisplay.Position = UDim2.new(0, 10, 0, 200)
debugDisplay.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
debugDisplay.BackgroundTransparency = 0.3
debugDisplay.BorderSizePixel = 0
debugDisplay.Visible = false
debugDisplay.ZIndex = 20

local debugCorner = Instance.new("UICorner")
debugCorner.CornerRadius = UDim.new(0, 10)
debugCorner.Parent = debugDisplay

local debugStroke = Instance.new("UIStroke")
debugStroke.Color = Color3.fromRGB(255, 255, 0)
debugStroke.Thickness = 2
debugStroke.Parent = debugDisplay

local debugTitle = Instance.new("TextLabel")
debugTitle.Name = "DebugTitle"
debugTitle.Parent = debugDisplay
debugTitle.Size = UDim2.new(1, 0, 0, 30)
debugTitle.Position = UDim2.new(0, 0, 0, 0)
debugTitle.BackgroundTransparency = 1
debugTitle.Text = "Debug Info - All UI Elements"
debugTitle.TextColor3 = Color3.fromRGB(255, 255, 0)
debugTitle.TextSize = 14
debugTitle.Font = Enum.Font.GothamBold
debugTitle.ZIndex = 21

local debugScrollFrame = Instance.new("ScrollingFrame")
debugScrollFrame.Name = "DebugScrollFrame"
debugScrollFrame.Parent = debugDisplay
debugScrollFrame.Size = UDim2.new(1, -10, 1, -40)
debugScrollFrame.Position = UDim2.new(0, 5, 0, 35)
debugScrollFrame.BackgroundTransparency = 1
debugScrollFrame.BorderSizePixel = 0
debugScrollFrame.ScrollBarThickness = 8
debugScrollFrame.ZIndex = 21

local debugTextLabel = Instance.new("TextLabel")
debugTextLabel.Name = "DebugTextLabel"
debugTextLabel.Parent = debugScrollFrame
debugTextLabel.Size = UDim2.new(1, -10, 0, 5000)
debugTextLabel.Position = UDim2.new(0, 0, 0, 0)
debugTextLabel.BackgroundTransparency = 1
debugTextLabel.Text = ""
debugTextLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
debugTextLabel.TextSize = 10
debugTextLabel.Font = Enum.Font.Code
debugTextLabel.TextXAlignment = Enum.TextXAlignment.Left
debugTextLabel.TextYAlignment = Enum.TextYAlignment.Top
debugTextLabel.TextWrapped = true
debugTextLabel.ZIndex = 21

local espFrame = Instance.new("Frame")
espFrame.Name = "ESPFrame"
espFrame.Parent = screenGui
espFrame.Size = UDim2.new(1, 0, 1, 0)
espFrame.Position = UDim2.new(0, 0, 0, 0)
espFrame.BackgroundTransparency = 1
espFrame.ZIndex = 1

local fovFrame = Instance.new("Frame")
fovFrame.Name = "FOVFrame"
fovFrame.Parent = screenGui
fovFrame.Size = UDim2.new(1, 0, 1, 0)
fovFrame.Position = UDim2.new(0, 0, 0, 0)
fovFrame.BackgroundTransparency = 1
fovFrame.ZIndex = 8

local autoAttackGUI = Instance.new("Frame")
autoAttackGUI.Name = "AutoAttackGUI"
autoAttackGUI.Parent = screenGui
autoAttackGUI.Size = UDim2.new(0, 140, 0, 90)
autoAttackGUI.Position = UDim2.new(0, 400, 0, 200)
autoAttackGUI.BackgroundColor3 = Color3.fromRGB(18, 18, 20)
autoAttackGUI.BackgroundTransparency = 0.1
autoAttackGUI.BorderSizePixel = 0
autoAttackGUI.Visible = false
autoAttackGUI.ZIndex = 15
autoAttackGUI.Active = true

local autoAttackGUICorner = Instance.new("UICorner")
autoAttackGUICorner.CornerRadius = UDim.new(0, 15)
autoAttackGUICorner.Parent = autoAttackGUI

local autoAttackGUIStroke = Instance.new("UIStroke")
autoAttackGUIStroke.Color = Color3.fromRGB(0, 255, 255)
autoAttackGUIStroke.Thickness = 2
autoAttackGUIStroke.Parent = autoAttackGUI

local autoAttackGUIGradient = Instance.new("UIGradient")
autoAttackGUIGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(18, 18, 20)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(25, 25, 30))
}
autoAttackGUIGradient.Rotation = 45
autoAttackGUIGradient.Parent = autoAttackGUI

local autoAttackGUITitle = Instance.new("TextLabel")
autoAttackGUITitle.Name = "Title"
autoAttackGUITitle.Parent = autoAttackGUI
autoAttackGUITitle.Size = UDim2.new(1, -10, 0, 35)
autoAttackGUITitle.Position = UDim2.new(0, 5, 0, 5)
autoAttackGUITitle.BackgroundTransparency = 1
autoAttackGUITitle.Text = "Auto Attack"
autoAttackGUITitle.TextColor3 = Color3.fromRGB(0, 200, 255)
autoAttackGUITitle.TextSize = 14
autoAttackGUITitle.TextXAlignment = Enum.TextXAlignment.Center
autoAttackGUITitle.Font = Enum.Font.GothamBold
autoAttackGUITitle.ZIndex = 16

local autoToggleContainer = Instance.new("Frame")
autoToggleContainer.Name = "AutoToggleContainer"
autoToggleContainer.Parent = autoAttackGUI
autoToggleContainer.Size = UDim2.new(0, 70, 0, 30)
autoToggleContainer.Position = UDim2.new(0.5, -35, 0, 50)
autoToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
autoToggleContainer.BorderSizePixel = 0
autoToggleContainer.ZIndex = 16

local autoToggleContainerCorner = Instance.new("UICorner")
autoToggleContainerCorner.CornerRadius = UDim.new(1, 0)
autoToggleContainerCorner.Parent = autoToggleContainer

local autoToggleBall = Instance.new("Frame")
autoToggleBall.Name = "AutoToggleBall"
autoToggleBall.Parent = autoToggleContainer
autoToggleBall.Size = UDim2.new(0, 26, 0, 26)
autoToggleBall.Position = UDim2.new(0, 2, 0, 2)
autoToggleBall.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
autoToggleBall.BorderSizePixel = 0
autoToggleBall.ZIndex = 17

local autoToggleBallCorner = Instance.new("UICorner")
autoToggleBallCorner.CornerRadius = UDim.new(1, 0)
autoToggleBallCorner.Parent = autoToggleBall

local autoToggleButton = Instance.new("TextButton")
autoToggleButton.Name = "AutoToggleButton"
autoToggleButton.Parent = autoToggleContainer
autoToggleButton.Size = UDim2.new(1, 0, 1, 0)
autoToggleButton.Position = UDim2.new(0, 0, 0, 0)
autoToggleButton.BackgroundTransparency = 1
autoToggleButton.Text = ""
autoToggleButton.ZIndex = 18

local chatWarGUI = Instance.new("Frame")
chatWarGUI.Name = "ChatWarGUI"
chatWarGUI.Parent = screenGui
chatWarGUI.Size = UDim2.new(0, 200, 0, 140)
chatWarGUI.Position = UDim2.new(0, 400, 0, 320)
chatWarGUI.BackgroundColor3 = Color3.fromRGB(18, 18, 20)
chatWarGUI.BackgroundTransparency = 0.1
chatWarGUI.BorderSizePixel = 0
chatWarGUI.Visible = false
chatWarGUI.ZIndex = 15
chatWarGUI.Active = true

local chatWarGUICorner = Instance.new("UICorner")
chatWarGUICorner.CornerRadius = UDim.new(0, 15)
chatWarGUICorner.Parent = chatWarGUI

local chatWarGUIStroke = Instance.new("UIStroke")
chatWarGUIStroke.Color = Color3.fromRGB(255, 100, 100)
chatWarGUIStroke.Thickness = 2
chatWarGUIStroke.Parent = chatWarGUI

local chatWarGUIGradient = Instance.new("UIGradient")
chatWarGUIGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(18, 18, 20)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(25, 25, 30))
}
chatWarGUIGradient.Rotation = 45
chatWarGUIGradient.Parent = chatWarGUI

local chatWarGUITitle = Instance.new("TextLabel")
chatWarGUITitle.Name = "Title"
chatWarGUITitle.Parent = chatWarGUI
chatWarGUITitle.Size = UDim2.new(1, -10, 0, 35)
chatWarGUITitle.Position = UDim2.new(0, 5, 0, 5)
chatWarGUITitle.BackgroundTransparency = 1
chatWarGUITitle.Text = "Chat War"
chatWarGUITitle.TextColor3 = Color3.fromRGB(255, 100, 100)
chatWarGUITitle.TextSize = 14
chatWarGUITitle.TextXAlignment = Enum.TextXAlignment.Center
chatWarGUITitle.Font = Enum.Font.GothamBold
chatWarGUITitle.ZIndex = 16

local chatDelayLabel = Instance.new("TextLabel")
chatDelayLabel.Name = "ChatDelayLabel"
chatDelayLabel.Parent = chatWarGUI
chatDelayLabel.Size = UDim2.new(0, 50, 0, 25)
chatDelayLabel.Position = UDim2.new(0, 10, 0, 45)
chatDelayLabel.BackgroundTransparency = 1
chatDelayLabel.Text = "Delay:"
chatDelayLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
chatDelayLabel.TextSize = 12
chatDelayLabel.TextXAlignment = Enum.TextXAlignment.Left
chatDelayLabel.Font = Enum.Font.Gotham
chatDelayLabel.ZIndex = 16

local chatDelayBox = Instance.new("TextBox")
chatDelayBox.Name = "ChatDelayBox"
chatDelayBox.Parent = chatWarGUI
chatDelayBox.Size = UDim2.new(0, 80, 0, 25)
chatDelayBox.Position = UDim2.new(0, 65, 0, 45)
chatDelayBox.BackgroundColor3 = Color3.fromRGB(35, 35, 40)
chatDelayBox.BorderSizePixel = 0
chatDelayBox.Text = "1"
chatDelayBox.TextColor3 = Color3.fromRGB(255, 255, 255)
chatDelayBox.TextSize = 12
chatDelayBox.Font = Enum.Font.Gotham
chatDelayBox.PlaceholderText = "Seconds"
chatDelayBox.PlaceholderColor3 = Color3.fromRGB(150, 150, 150)
chatDelayBox.ZIndex = 16

local chatDelayBoxCorner = Instance.new("UICorner")
chatDelayBoxCorner.CornerRadius = UDim.new(0, 12)
chatDelayBoxCorner.Parent = chatDelayBox

local chatDelayBoxStroke = Instance.new("UIStroke")
chatDelayBoxStroke.Color = Color3.fromRGB(255, 100, 100)
chatDelayBoxStroke.Thickness = 1
chatDelayBoxStroke.Parent = chatDelayBox

local chatToggleContainer = Instance.new("Frame")
chatToggleContainer.Name = "ChatToggleContainer"
chatToggleContainer.Parent = chatWarGUI
chatToggleContainer.Size = UDim2.new(0, 70, 0, 30)
chatToggleContainer.Position = UDim2.new(0.5, -35, 0, 90)
chatToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
chatToggleContainer.BorderSizePixel = 0
chatToggleContainer.ZIndex = 16

local chatToggleContainerCorner = Instance.new("UICorner")
chatToggleContainerCorner.CornerRadius = UDim.new(1, 0)
chatToggleContainerCorner.Parent = chatToggleContainer

local chatToggleBall = Instance.new("Frame")
chatToggleBall.Name = "ChatToggleBall"
chatToggleBall.Parent = chatToggleContainer
chatToggleBall.Size = UDim2.new(0, 26, 0, 26)
chatToggleBall.Position = UDim2.new(0, 2, 0, 2)
chatToggleBall.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
chatToggleBall.BorderSizePixel = 0
chatToggleBall.ZIndex = 17

local chatToggleBallCorner = Instance.new("UICorner")
chatToggleBallCorner.CornerRadius = UDim.new(1, 0)
chatToggleBallCorner.Parent = chatToggleBall

local chatToggleButton = Instance.new("TextButton")
chatToggleButton.Name = "ChatToggleButton"
chatToggleButton.Parent = chatToggleContainer
chatToggleButton.Size = UDim2.new(1, 0, 1, 0)
chatToggleButton.Position = UDim2.new(0, 0, 0, 0)
chatToggleButton.BackgroundTransparency = 1
chatToggleButton.Text = ""
chatToggleButton.ZIndex = 18

local speedHackGUI = Instance.new("Frame")
speedHackGUI.Name = "SpeedHackGUI"
speedHackGUI.Parent = screenGui
speedHackGUI.Size = UDim2.new(0, 220, 0, 120)
speedHackGUI.Position = UDim2.new(0, 600, 0, 200)
speedHackGUI.BackgroundColor3 = Color3.fromRGB(18, 18, 20)
speedHackGUI.BackgroundTransparency = 0.1
speedHackGUI.BorderSizePixel = 0
speedHackGUI.Visible = false
speedHackGUI.ZIndex = 15
speedHackGUI.Active = true

local speedHackGUICorner = Instance.new("UICorner")
speedHackGUICorner.CornerRadius = UDim.new(0, 15)
speedHackGUICorner.Parent = speedHackGUI

local speedHackGUIStroke = Instance.new("UIStroke")
speedHackGUIStroke.Color = Color3.fromRGB(100, 255, 100)
speedHackGUIStroke.Thickness = 2
speedHackGUIStroke.Parent = speedHackGUI

local speedHackGUIGradient = Instance.new("UIGradient")
speedHackGUIGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(18, 18, 20)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(25, 25, 30))
}
speedHackGUIGradient.Rotation = 45
speedHackGUIGradient.Parent = speedHackGUI

local speedHackGUITitle = Instance.new("TextLabel")
speedHackGUITitle.Name = "Title"
speedHackGUITitle.Parent = speedHackGUI
speedHackGUITitle.Size = UDim2.new(1, -10, 0, 30)
speedHackGUITitle.Position = UDim2.new(0, 5, 0, 5)
speedHackGUITitle.BackgroundTransparency = 1
speedHackGUITitle.Text = "Hack Speed"
speedHackGUITitle.TextColor3 = Color3.fromRGB(100, 255, 100)
speedHackGUITitle.TextSize = 14
speedHackGUITitle.TextXAlignment = Enum.TextXAlignment.Center
speedHackGUITitle.Font = Enum.Font.GothamBold
speedHackGUITitle.ZIndex = 16

local speedInputLabel = Instance.new("TextLabel")
speedInputLabel.Name = "SpeedInputLabel"
speedInputLabel.Parent = speedHackGUI
speedInputLabel.Size = UDim2.new(0, 50, 0, 25)
speedInputLabel.Position = UDim2.new(0, 10, 0, 40)
speedInputLabel.BackgroundTransparency = 1
speedInputLabel.Text = "Speed:"
speedInputLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
speedInputLabel.TextSize = 12
speedInputLabel.TextXAlignment = Enum.TextXAlignment.Left
speedInputLabel.Font = Enum.Font.Gotham
speedInputLabel.ZIndex = 16

local speedInputBox = Instance.new("TextBox")
speedInputBox.Name = "SpeedInputBox"
speedInputBox.Parent = speedHackGUI
speedInputBox.Size = UDim2.new(0, 140, 0, 25)
speedInputBox.Position = UDim2.new(0, 65, 0, 40)
speedInputBox.BackgroundColor3 = Color3.fromRGB(35, 35, 40)
speedInputBox.BorderSizePixel = 0
speedInputBox.Text = "3.0"
speedInputBox.TextColor3 = Color3.fromRGB(255, 255, 255)
speedInputBox.TextSize = 12
speedInputBox.Font = Enum.Font.Gotham
speedInputBox.PlaceholderText = "Ví Dụ: 3.0 là X3 Speed"
speedInputBox.PlaceholderColor3 = Color3.fromRGB(150, 150, 150)
speedInputBox.ZIndex = 16

local speedInputBoxCorner = Instance.new("UICorner")
speedInputBoxCorner.CornerRadius = UDim.new(0, 12)
speedInputBoxCorner.Parent = speedInputBox

local speedInputBoxStroke = Instance.new("UIStroke")
speedInputBoxStroke.Color = Color3.fromRGB(100, 255, 100)
speedInputBoxStroke.Thickness = 1
speedInputBoxStroke.Parent = speedInputBox

local speedHackToggleContainer = Instance.new("Frame")
speedHackToggleContainer.Name = "SpeedHackToggleContainer"
speedHackToggleContainer.Parent = speedHackGUI
speedHackToggleContainer.Size = UDim2.new(0, 70, 0, 30)
speedHackToggleContainer.Position = UDim2.new(0.5, -35, 0, 80)
speedHackToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
speedHackToggleContainer.BorderSizePixel = 0
speedHackToggleContainer.ZIndex = 16

local speedHackToggleContainerCorner = Instance.new("UICorner")
speedHackToggleContainerCorner.CornerRadius = UDim.new(1, 0)
speedHackToggleContainerCorner.Parent = speedHackToggleContainer

local speedHackToggleBall = Instance.new("Frame")
speedHackToggleBall.Name = "SpeedHackToggleBall"
speedHackToggleBall.Parent = speedHackToggleContainer
speedHackToggleBall.Size = UDim2.new(0, 26, 0, 26)
speedHackToggleBall.Position = UDim2.new(0, 2, 0, 2)
speedHackToggleBall.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
speedHackToggleBall.BorderSizePixel = 0
speedHackToggleBall.ZIndex = 17

local speedHackToggleBallCorner = Instance.new("UICorner")
speedHackToggleBallCorner.CornerRadius = UDim.new(1, 0)
speedHackToggleBallCorner.Parent = speedHackToggleBall

local speedHackToggleButton = Instance.new("TextButton")
speedHackToggleButton.Name = "SpeedHackToggleButton"
speedHackToggleButton.Parent = speedHackToggleContainer
speedHackToggleButton.Size = UDim2.new(1, 0, 1, 0)
speedHackToggleButton.Position = UDim2.new(0, 0, 0, 0)
speedHackToggleButton.BackgroundTransparency = 1
speedHackToggleButton.Text = ""
speedHackToggleButton.ZIndex = 18

local autoFarmGUI = Instance.new("Frame")
autoFarmGUI.Name = "AutoFarmGUI"
autoFarmGUI.Parent = screenGui
autoFarmGUI.Size = UDim2.new(0, 200, 0, 120)
autoFarmGUI.Position = UDim2.new(0, 350, 0, 350)
autoFarmGUI.BackgroundColor3 = Color3.fromRGB(18, 18, 20)
autoFarmGUI.BackgroundTransparency = 0.1
autoFarmGUI.BorderSizePixel = 0
autoFarmGUI.Visible = false
autoFarmGUI.ZIndex = 15
autoFarmGUI.Active = true

local autoFarmGUICorner = Instance.new("UICorner")
autoFarmGUICorner.CornerRadius = UDim.new(0, 15)
autoFarmGUICorner.Parent = autoFarmGUI

local autoFarmGUIStroke = Instance.new("UIStroke")
autoFarmGUIStroke.Color = Color3.fromRGB(255, 200, 0)
autoFarmGUIStroke.Thickness = 2
autoFarmGUIStroke.Parent = autoFarmGUI

local autoFarmGUIGradient = Instance.new("UIGradient")
autoFarmGUIGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(18, 18, 20)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(25, 25, 30))
}
autoFarmGUIGradient.Rotation = 45
autoFarmGUIGradient.Parent = autoFarmGUI

local autoFarmGUITitle = Instance.new("TextLabel")
autoFarmGUITitle.Name = "Title"
autoFarmGUITitle.Parent = autoFarmGUI
autoFarmGUITitle.Size = UDim2.new(1, -10, 0, 30)
autoFarmGUITitle.Position = UDim2.new(0, 5, 0, 5)
autoFarmGUITitle.BackgroundTransparency = 1
autoFarmGUITitle.Text = "Auto Farm Level"
autoFarmGUITitle.TextColor3 = Color3.fromRGB(255, 200, 0)
autoFarmGUITitle.TextSize = 14
autoFarmGUITitle.TextXAlignment = Enum.TextXAlignment.Center
autoFarmGUITitle.Font = Enum.Font.GothamBold
autoFarmGUITitle.ZIndex = 16

local autoJumpGUI = Instance.new("Frame")
autoJumpGUI.Name = "AutoJumpGUI"
autoJumpGUI.Parent = screenGui
autoJumpGUI.Size = UDim2.new(0, 140, 0, 90)
autoJumpGUI.Position = UDim2.new(0, 600, 0, 350)
autoJumpGUI.BackgroundColor3 = Color3.fromRGB(18, 18, 20)
autoJumpGUI.BackgroundTransparency = 0.1
autoJumpGUI.BorderSizePixel = 0
autoJumpGUI.Visible = false
autoJumpGUI.ZIndex = 15
autoJumpGUI.Active = true

local aimbotGUI = Instance.new("Frame")
aimbotGUI.Name = "AimbotGUI"
aimbotGUI.Parent = screenGui
aimbotGUI.Size = UDim2.new(0, 250, 0, 200)
aimbotGUI.Position = UDim2.new(0, 380, 0, 470)
aimbotGUI.BackgroundColor3 = Color3.fromRGB(18, 18, 20)
aimbotGUI.BackgroundTransparency = 0.1
aimbotGUI.BorderSizePixel = 0
aimbotGUI.Visible = false
aimbotGUI.ZIndex = 15
aimbotGUI.Active = true

local aimbotGUICorner = Instance.new("UICorner")
aimbotGUICorner.CornerRadius = UDim.new(0, 15)
aimbotGUICorner.Parent = aimbotGUI

local aimbotGUIStroke = Instance.new("UIStroke")
aimbotGUIStroke.Color = Color3.fromRGB(255, 0, 100)
aimbotGUIStroke.Thickness = 2
aimbotGUIStroke.Parent = aimbotGUI

local aimbotGUIGradient = Instance.new("UIGradient")
aimbotGUIGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(18, 18, 20)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(25, 25, 30))
}
aimbotGUIGradient.Rotation = 45
aimbotGUIGradient.Parent = aimbotGUI

local aimbotGUITitle = Instance.new("TextLabel")
aimbotGUITitle.Name = "Title"
aimbotGUITitle.Parent = aimbotGUI
aimbotGUITitle.Size = UDim2.new(1, -10, 0, 30)
aimbotGUITitle.Position = UDim2.new(0, 5, 0, 5)
aimbotGUITitle.BackgroundTransparency = 1
aimbotGUITitle.Text = "Aimbot"
aimbotGUITitle.TextColor3 = Color3.fromRGB(255, 0, 100)
aimbotGUITitle.TextSize = 14
aimbotGUITitle.TextXAlignment = Enum.TextXAlignment.Center
aimbotGUITitle.Font = Enum.Font.GothamBold
aimbotGUITitle.ZIndex = 16

local targetDropdown = Instance.new("TextButton")
targetDropdown.Name = "TargetDropdown"
targetDropdown.Parent = aimbotGUI
targetDropdown.Size = UDim2.new(0, 160, 0, 25)
targetDropdown.Position = UDim2.new(0, 10, 0, 40)
targetDropdown.BackgroundColor3 = Color3.fromRGB(35, 35, 40)
targetDropdown.BorderSizePixel = 0
targetDropdown.Text = "Chọn mục tiêu"
targetDropdown.TextColor3 = Color3.fromRGB(255, 255, 255)
targetDropdown.TextSize = 11
targetDropdown.Font = Enum.Font.Gotham
targetDropdown.ZIndex = 16

local dropdownCorner = Instance.new("UICorner")
dropdownCorner.CornerRadius = UDim.new(0, 12)
dropdownCorner.Parent = targetDropdown

local dropdownStroke = Instance.new("UIStroke")
dropdownStroke.Color = Color3.fromRGB(255, 0, 100)
dropdownStroke.Thickness = 1
dropdownStroke.Parent = targetDropdown

local refreshButton = Instance.new("TextButton")
refreshButton.Name = "RefreshButton"
refreshButton.Parent = aimbotGUI
refreshButton.Size = UDim2.new(0, 60, 0, 25)
refreshButton.Position = UDim2.new(0, 180, 0, 40)
refreshButton.BackgroundColor3 = Color3.fromRGB(0, 150, 255)
refreshButton.BorderSizePixel = 0
refreshButton.Text = "Refresh"
refreshButton.TextColor3 = Color3.fromRGB(255, 255, 255)
refreshButton.TextSize = 10
refreshButton.Font = Enum.Font.GothamBold
refreshButton.ZIndex = 16

local refreshCorner = Instance.new("UICorner")
refreshCorner.CornerRadius = UDim.new(0, 12)
refreshCorner.Parent = refreshButton

local dropdownList = Instance.new("ScrollingFrame")
dropdownList.Name = "DropdownList"
dropdownList.Parent = aimbotGUI
dropdownList.Size = UDim2.new(0, 160, 0, 0)
dropdownList.Position = UDim2.new(0, 10, 0, 65)
dropdownList.BackgroundColor3 = Color3.fromRGB(25, 25, 30)
dropdownList.BorderSizePixel = 0
dropdownList.Visible = false
dropdownList.ScrollBarThickness = 4
dropdownList.ZIndex = 20

local dropdownListCorner = Instance.new("UICorner")
dropdownListCorner.CornerRadius = UDim.new(0, 8)
dropdownListCorner.Parent = dropdownList

local fovLabel = Instance.new("TextLabel")
fovLabel.Name = "FOVLabel"
fovLabel.Parent = aimbotGUI
fovLabel.Size = UDim2.new(0, 60, 0, 20)
fovLabel.Position = UDim2.new(0, 10, 0, 80)
fovLabel.BackgroundTransparency = 1
fovLabel.Text = "FOV: 100"
fovLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
fovLabel.TextSize = 11
fovLabel.Font = Enum.Font.Gotham
fovLabel.ZIndex = 16

local fovSlider = Instance.new("Frame")
fovSlider.Name = "FOVSlider"
fovSlider.Parent = aimbotGUI
fovSlider.Size = UDim2.new(0, 170, 0, 6)
fovSlider.Position = UDim2.new(0, 70, 0, 87)
fovSlider.BackgroundColor3 = Color3.fromRGB(50, 50, 55)
fovSlider.BorderSizePixel = 0
fovSlider.ZIndex = 16

local fovSliderCorner = Instance.new("UICorner")
fovSliderCorner.CornerRadius = UDim.new(1, 0)
fovSliderCorner.Parent = fovSlider

local fovSliderBall = Instance.new("Frame")
fovSliderBall.Name = "FOVSliderBall"
fovSliderBall.Parent = fovSlider
fovSliderBall.Size = UDim2.new(0, 16, 0, 16)
fovSliderBall.Position = UDim2.new(0, 77, 0, -5)
fovSliderBall.BackgroundColor3 = Color3.fromRGB(255, 0, 100)
fovSliderBall.BorderSizePixel = 0
fovSliderBall.ZIndex = 17

local fovSliderBallCorner = Instance.new("UICorner")
fovSliderBallCorner.CornerRadius = UDim.new(1, 0)
fovSliderBallCorner.Parent = fovSliderBall

local aimbotToggleContainer = Instance.new("Frame")
aimbotToggleContainer.Name = "AimbotToggleContainer"
aimbotToggleContainer.Parent = aimbotGUI
aimbotToggleContainer.Size = UDim2.new(0, 70, 0, 30)
aimbotToggleContainer.Position = UDim2.new(0.5, -35, 0, 120)
aimbotToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
aimbotToggleContainer.BorderSizePixel = 0
aimbotToggleContainer.ZIndex = 16

local aimbotToggleContainerCorner = Instance.new("UICorner")
aimbotToggleContainerCorner.CornerRadius = UDim.new(1, 0)
aimbotToggleContainerCorner.Parent = aimbotToggleContainer

local aimbotToggleBall = Instance.new("Frame")
aimbotToggleBall.Name = "AimbotToggleBall"
aimbotToggleBall.Parent = aimbotToggleContainer
aimbotToggleBall.Size = UDim2.new(0, 26, 0, 26)
aimbotToggleBall.Position = UDim2.new(0, 2, 0, 2)
aimbotToggleBall.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
aimbotToggleBall.BorderSizePixel = 0
aimbotToggleBall.ZIndex = 17

local aimbotToggleBallCorner = Instance.new("UICorner")
aimbotToggleBallCorner.CornerRadius = UDim.new(1, 0)
aimbotToggleBallCorner.Parent = aimbotToggleBall

local aimbotToggleButton = Instance.new("TextButton")
aimbotToggleButton.Name = "AimbotToggleButton"
aimbotToggleButton.Parent = aimbotToggleContainer
aimbotToggleButton.Size = UDim2.new(1, 0, 1, 0)
aimbotToggleButton.Position = UDim2.new(0, 0, 0, 0)
aimbotToggleButton.BackgroundTransparency = 1
aimbotToggleButton.Text = ""
aimbotToggleButton.ZIndex = 18

local autoJumpGUICorner = Instance.new("UICorner")
autoJumpGUICorner.CornerRadius = UDim.new(0, 15)
autoJumpGUICorner.Parent = autoJumpGUI

local autoJumpGUIStroke = Instance.new("UIStroke")
autoJumpGUIStroke.Color = Color3.fromRGB(255, 0, 255)
autoJumpGUIStroke.Thickness = 2
autoJumpGUIStroke.Parent = autoJumpGUI

local autoJumpGUIGradient = Instance.new("UIGradient")
autoJumpGUIGradient.Color = ColorSequence.new{
    ColorSequenceKeypoint.new(0, Color3.fromRGB(18, 18, 20)),
    ColorSequenceKeypoint.new(1, Color3.fromRGB(25, 25, 30))
}
autoJumpGUIGradient.Rotation = 45
autoJumpGUIGradient.Parent = autoJumpGUI

local autoJumpGUITitle = Instance.new("TextLabel")
autoJumpGUITitle.Name = "Title"
autoJumpGUITitle.Parent = autoJumpGUI
autoJumpGUITitle.Size = UDim2.new(1, -10, 0, 35)
autoJumpGUITitle.Position = UDim2.new(0, 5, 0, 5)
autoJumpGUITitle.BackgroundTransparency = 1
autoJumpGUITitle.Text = "Auto Jump"
autoJumpGUITitle.TextColor3 = Color3.fromRGB(255, 0, 255)
autoJumpGUITitle.TextSize = 14
autoJumpGUITitle.TextXAlignment = Enum.TextXAlignment.Center
autoJumpGUITitle.Font = Enum.Font.GothamBold
autoJumpGUITitle.ZIndex = 16

local jumpToggleContainer = Instance.new("Frame")
jumpToggleContainer.Name = "JumpToggleContainer"
jumpToggleContainer.Parent = autoJumpGUI
jumpToggleContainer.Size = UDim2.new(0, 70, 0, 30)
jumpToggleContainer.Position = UDim2.new(0.5, -35, 0, 50)
jumpToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
jumpToggleContainer.BorderSizePixel = 0
jumpToggleContainer.ZIndex = 16

local jumpToggleContainerCorner = Instance.new("UICorner")
jumpToggleContainerCorner.CornerRadius = UDim.new(1, 0)
jumpToggleContainerCorner.Parent = jumpToggleContainer

local jumpToggleBall = Instance.new("Frame")
jumpToggleBall.Name = "JumpToggleBall"
jumpToggleBall.Parent = jumpToggleContainer
jumpToggleBall.Size = UDim2.new(0, 26, 0, 26)
jumpToggleBall.Position = UDim2.new(0, 2, 0, 2)
jumpToggleBall.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
jumpToggleBall.BorderSizePixel = 0
jumpToggleBall.ZIndex = 17

local jumpToggleBallCorner = Instance.new("UICorner")
jumpToggleBallCorner.CornerRadius = UDim.new(1, 0)
jumpToggleBallCorner.Parent = jumpToggleBall

local jumpToggleButton = Instance.new("TextButton")
jumpToggleButton.Name = "JumpToggleButton"
jumpToggleButton.Parent = jumpToggleContainer
jumpToggleButton.Size = UDim2.new(1, 0, 1, 0)
jumpToggleButton.Position = UDim2.new(0, 0, 0, 0)
jumpToggleButton.BackgroundTransparency = 1
jumpToggleButton.Text = ""
jumpToggleButton.ZIndex = 18

local farmStatusLabel = Instance.new("TextLabel")
farmStatusLabel.Name = "FarmStatusLabel"
farmStatusLabel.Parent = autoFarmGUI
farmStatusLabel.Size = UDim2.new(1, -10, 0, 50)
farmStatusLabel.Position = UDim2.new(0, 5, 0, 40)
farmStatusLabel.BackgroundTransparency = 1
farmStatusLabel.Text = "Status: Tìm kiếm NPC..."
farmStatusLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
farmStatusLabel.TextSize = 11
farmStatusLabel.TextWrapped = true
farmStatusLabel.TextXAlignment = Enum.TextXAlignment.Center
farmStatusLabel.Font = Enum.Font.Gotham
farmStatusLabel.ZIndex = 16

local farmToggleContainer = Instance.new("Frame")
farmToggleContainer.Name = "FarmToggleContainer"
farmToggleContainer.Parent = autoFarmGUI
farmToggleContainer.Size = UDim2.new(0, 70, 0, 30)
farmToggleContainer.Position = UDim2.new(0.5, -35, 0, 85)
farmToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
farmToggleContainer.BorderSizePixel = 0
farmToggleContainer.ZIndex = 16

local farmToggleContainerCorner = Instance.new("UICorner")
farmToggleContainerCorner.CornerRadius = UDim.new(1, 0)
farmToggleContainerCorner.Parent = farmToggleContainer

local farmToggleBall = Instance.new("Frame")
farmToggleBall.Name = "FarmToggleBall"
farmToggleBall.Parent = farmToggleContainer
farmToggleBall.Size = UDim2.new(0, 26, 0, 26)
farmToggleBall.Position = UDim2.new(0, 2, 0, 2)
farmToggleBall.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
farmToggleBall.BorderSizePixel = 0
farmToggleBall.ZIndex = 17

local farmToggleBallCorner = Instance.new("UICorner")
farmToggleBallCorner.CornerRadius = UDim.new(1, 0)
farmToggleBallCorner.Parent = farmToggleBall

local farmToggleButton = Instance.new("TextButton")
farmToggleButton.Name = "FarmToggleButton"
farmToggleButton.Parent = farmToggleContainer
farmToggleButton.Size = UDim2.new(1, 0, 1, 0)
farmToggleButton.Position = UDim2.new(0, 0, 0, 0)
farmToggleButton.BackgroundTransparency = 1
farmToggleButton.Text = ""
farmToggleButton.ZIndex = 18

local function createESP(character)
    if not character or not character:FindFirstChild("HumanoidRootPart") then return end
    
    local espContainer = Instance.new("Frame")
    espContainer.Name = "ESP_" .. character.Name
    espContainer.Parent = espFrame
    espContainer.Size = UDim2.new(0, 220, 0, 25)
    espContainer.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
    espContainer.BackgroundTransparency = 0.1
    espContainer.BorderSizePixel = 0
    espContainer.ZIndex = 10
    
    local espCorner = Instance.new("UICorner")
    espCorner.CornerRadius = UDim.new(0, 10)
    espCorner.Parent = espContainer
    
    local espStroke = Instance.new("UIStroke")
    espStroke.Color = Color3.fromRGB(0, 255, 255)
    espStroke.Thickness = 2
    espStroke.Parent = espContainer
    
    local espLabel = Instance.new("TextLabel")
    espLabel.Name = "ESPLabel"
    espLabel.Parent = espContainer
    espLabel.Size = UDim2.new(1, -10, 1, 0)
    espLabel.Position = UDim2.new(0, 5, 0, 0)
    espLabel.BackgroundTransparency = 1
    espLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
    espLabel.TextSize = 11
    espLabel.TextStrokeTransparency = 0
    espLabel.TextStrokeColor3 = Color3.fromRGB(0, 0, 0)
    espLabel.Font = Enum.Font.GothamBold
    espLabel.ZIndex = 11
    espLabel.TextXAlignment = Enum.TextXAlignment.Center
    espLabel.TextYAlignment = Enum.TextYAlignment.Center
    
    espElements[character] = espContainer
end

local function createFOVCircle()
    if fovCircle then
        fovCircle:Destroy()
    end
    
    fovCircle = Instance.new("Frame")
    fovCircle.Name = "FOVCircle"
    fovCircle.Parent = fovFrame
    fovCircle.Size = UDim2.new(0, fovSize * 2, 0, fovSize * 2)
    fovCircle.Position = UDim2.new(0.5, -fovSize, 0.5, -fovSize)
    fovCircle.BackgroundTransparency = 1
    fovCircle.BorderSizePixel = 0
    fovCircle.ZIndex = 9
    fovCircle.Visible = false
    
    local stroke = Instance.new("UIStroke")
    stroke.Color = Color3.fromRGB(0, 255, 0)
    stroke.Thickness = 2
    stroke.Parent = fovCircle
    
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(1, 0)
    corner.Parent = fovCircle
end

local function updateESP()
    if not espEnabled then return end
    
    local playerChar = player.Character
    if not playerChar or not playerChar:FindFirstChild("HumanoidRootPart") then return end
    
    for character, espContainer in pairs(espElements) do
        if character and character.Parent and character:FindFirstChild("HumanoidRootPart") and character:FindFirstChild("Head") then
            local headPos = character.Head.Position
            local screenPos, onScreen = camera:WorldToScreenPoint(headPos + Vector3.new(0, 3, 0))
            
            if onScreen then
                local distance = math.floor((playerChar.HumanoidRootPart.Position - character.HumanoidRootPart.Position).Magnitude)
                
                local espLabel = espContainer:FindFirstChild("ESPLabel")
                if espLabel then
                    espLabel.Text = "Name: " .. character.Name .. " | Khoảng Cách: " .. distance .. "m"
                end
                
                espContainer.Position = UDim2.new(0, screenPos.X - 110, 0, screenPos.Y - 12)
                espContainer.Visible = true
            else
                espContainer.Visible = false
            end
        else
            if espContainer then
                espContainer:Destroy()
            end
            espElements[character] = nil
        end
    end
end

local function scanForCharacters()
    if not espEnabled then return end
    
    for _, otherPlayer in pairs(Players:GetPlayers()) do
        if otherPlayer ~= player and otherPlayer.Character and otherPlayer.Character:FindFirstChild("HumanoidRootPart") then
            if not espElements[otherPlayer.Character] then
                createESP(otherPlayer.Character)
            end
        end
    end
    
    for _, obj in pairs(Workspace:GetDescendants()) do
        if obj:IsA("Model") and obj:FindFirstChildOfClass("Humanoid") and not Players:GetPlayerFromCharacter(obj) then
            if not espElements[obj] and obj:FindFirstChild("HumanoidRootPart") then
                createESP(obj)
            end
        end
    end
end

local function toggleESP()
    espEnabled = not espEnabled
    
    if espEnabled then
        espToggle.Text = "ON"
        espToggle.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        espToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(0, 200, 80)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(0, 150, 60))
        }
        scanForCharacters()
        statusLabel.Text = "ESP: ON"
    else
        espToggle.Text = "OFF"
        espToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        espToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
        }
        
        for character, espContainer in pairs(espElements) do
            if espContainer then
                espContainer:Destroy()
            end
        end
        espElements = {}
        statusLabel.Text = "ESP: OFF"
    end
end

local function startAutoJump()
    if autoJumpConnection then
        autoJumpConnection:Disconnect()
    end
    
    autoJumpConnection = spawn(function()
        while autoJumpEnabled do
            if player.Character and player.Character:FindFirstChild("Humanoid") then
                local humanoid = player.Character.Humanoid
                humanoid.Jump = true
                wait(0.01)
                humanoid.Jump = false
            end
            wait(0.1)
        end
    end)
end

local function stopAutoJump()
    if autoJumpConnection then
        autoJumpConnection:Disconnect()
        autoJumpConnection = nil
    end
end

local function toggleAutoJump()
    autoJumpEnabled = not autoJumpEnabled
    
    if autoJumpEnabled then
        jumpToggle.Text = "ON"
        jumpToggle.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        jumpToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(0, 200, 80)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(0, 150, 60))
        }
        
        jumpToggleContainer.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        local tween = TweenService:Create(jumpToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 42, 0, 2)}
        )
        tween:Play()
        
        autoJumpGUIVisible = true
        autoJumpGUI.Visible = true
        startAutoJump()
        statusLabel.Text = "Auto Jump: ON"
    else
        jumpToggle.Text = "OFF"
        jumpToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        jumpToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
        }
        
        jumpToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        local tween = TweenService:Create(jumpToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 2, 0, 2)}
        )
        tween:Play()
        
        autoJumpGUIVisible = false
        autoJumpGUI.Visible = false
        stopAutoJump()
        statusLabel.Text = "Auto Jump: OFF"
    end
end

local function toggleAutoJumpGUI()
    autoJumpEnabled = not autoJumpEnabled
    
    if autoJumpEnabled then
        jumpToggleContainer.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        local tween = TweenService:Create(jumpToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 42, 0, 2)}
        )
        tween:Play()
        startAutoJump()
    else
        jumpToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        local tween = TweenService:Create(jumpToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 2, 0, 2)}
        )
        tween:Play()
        stopAutoJump()
    end
end

local function applySpeedHack()
    if speedHackConnection then
        speedHackConnection:Disconnect()
    end
    
    speedHackConnection = RunService.RenderStepped:Connect(function()
        if speedHackEnabled and player.Character and player.Character:FindFirstChild("HumanoidRootPart") and player.Character:FindFirstChild("Humanoid") then
            local humanoid = player.Character.Humanoid
            local rootPart = player.Character.HumanoidRootPart
            
            if humanoid.MoveDirection.Magnitude > 0 then
                local speed = (customSpeed - 1) * 0.5
                rootPart.CFrame = rootPart.CFrame + (humanoid.MoveDirection * speed)
            end
            
            humanoid.WalkSpeed = originalWalkSpeed
        end
    end)
end

local function stopSpeedHack()
    if speedHackConnection then
        speedHackConnection:Disconnect()
        speedHackConnection = nil
    end
    
    if player.Character and player.Character:FindFirstChild("Humanoid") then
        player.Character.Humanoid.WalkSpeed = originalWalkSpeed
    end
end

local function toggleSpeedHack()
    speedHackEnabled = not speedHackEnabled
    
    if speedHackEnabled then
        local inputSpeed = tonumber(speedInputBox.Text) or 3.0
        if inputSpeed > 10.0 then
            inputSpeed = 10.0
            speedInputBox.Text = "10.0"
        elseif inputSpeed < 1.0 then
            inputSpeed = 1.0
            speedInputBox.Text = "1.0"
        end
        customSpeed = inputSpeed
        
        speedToggle.Text = "ON"
        speedToggle.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        speedToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(0, 200, 80)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(0, 150, 60))
        }
        
        speedHackToggleContainer.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        local tween = TweenService:Create(speedHackToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 42, 0, 2)}
        )
        tween:Play()
        
        speedHackGUIVisible = true
        speedHackGUI.Visible = true
        applySpeedHack()
        statusLabel.Text = "Speed Hack: ON - " .. customSpeed .. "x Speed"
    else
        speedToggle.Text = "OFF"
        speedToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        speedToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
        }
        
        speedHackToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        local tween = TweenService:Create(speedHackToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 2, 0, 2)}
        )
        tween:Play()
        
        speedHackGUIVisible = false
        speedHackGUI.Visible = false
        stopSpeedHack()
        statusLabel.Text = "Speed Hack: OFF"
    end
end

local function toggleSpeedHackGUI()
    speedHackEnabled = not speedHackEnabled
    
    if speedHackEnabled then
        local inputSpeed = tonumber(speedInputBox.Text) or 3.0
        if inputSpeed > 10.0 then
            inputSpeed = 10.0
            speedInputBox.Text = "10.0"
        elseif inputSpeed < 1.0 then
            inputSpeed = 1.0
            speedInputBox.Text = "1.0"
        end
        customSpeed = inputSpeed
        
        speedHackToggleContainer.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        local tween = TweenService:Create(speedHackToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 42, 0, 2)}
        )
        tween:Play()
        applySpeedHack()
    else
        speedHackToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        local tween = TweenService:Create(speedHackToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 2, 0, 2)}
        )
        tween:Play()
        stopSpeedHack()
    end
end

local function startAutoAttack()
    if autoAttackConnection then
        autoAttackConnection:Disconnect()
    end
    
    autoAttackConnection = RunService.Heartbeat:Connect(function()
        if autoAttackEnabled then
            VirtualUser:CaptureController()
            VirtualUser:ClickButton1(Vector2.new(camera.ViewportSize.X/2, camera.ViewportSize.Y/2))
        end
    end)
end

local function stopAutoAttack()
    if autoAttackConnection then
        autoAttackConnection:Disconnect()
        autoAttackConnection = nil
    end
end

local function toggleAutoAttack()
    autoAttackEnabled = not autoAttackEnabled
    
    if autoAttackEnabled then
        autoAttackToggle.Text = "ON"
        autoAttackToggle.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        autoAttackToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(0, 200, 80)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(0, 150, 60))
        }
        
        autoToggleContainer.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        local tween = TweenService:Create(autoToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 42, 0, 2)}
        )
        tween:Play()
        
        autoAttackGUIVisible = true
        autoAttackGUI.Visible = true
        startAutoAttack()
        statusLabel.Text = "Auto Attack: ON"
    else
        autoAttackToggle.Text = "OFF"
        autoAttackToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        autoAttackToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
        }
        
        autoToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        local tween = TweenService:Create(autoToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 2, 0, 2)}
        )
        tween:Play()
        
        autoAttackGUIVisible = false
        autoAttackGUI.Visible = false
        stopAutoAttack()
        statusLabel.Text = "Auto Attack: OFF"
    end
end

local function toggleAutoAttackGUI()
    autoAttackEnabled = not autoAttackEnabled
    
    if autoAttackEnabled then
        autoToggleContainer.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        local tween = TweenService:Create(autoToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 42, 0, 2)}
        )
        tween:Play()
        startAutoAttack()
    else
        autoToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        local tween = TweenService:Create(autoToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 2, 0, 2)}
        )
        tween:Play()
        stopAutoAttack()
    end
end

local function enableNoclip()
    if player.Character then
        for _, part in pairs(player.Character:GetChildren()) do
            if part:IsA("BasePart") then
                part.CanCollide = false
            end
        end
    end
end

local function disableNoclip()
    if player.Character then
        for _, part in pairs(player.Character:GetChildren()) do
            if part:IsA("BasePart") and part.Name ~= "HumanoidRootPart" then
                part.CanCollide = true
            end
        end
    end
end

local function findNearestNPC()
    if not player.Character or not player.Character:FindFirstChild("HumanoidRootPart") then
        return nil
    end
    
    local playerPos = player.Character.HumanoidRootPart.Position
    local nearestNPC = nil
    local shortestDistance = math.huge
    local foundNPCs = 0
    
    print("=== DEBUG: Tìm kiếm NPC ===")
    
    for _, obj in pairs(Workspace:GetDescendants()) do
        if obj:IsA("Model") and obj:FindFirstChildOfClass("Humanoid") and not Players:GetPlayerFromCharacter(obj) then
            if obj:FindFirstChild("HumanoidRootPart") then
                local humanoid = obj:FindFirstChildOfClass("Humanoid")
                if humanoid and humanoid.Health > 0 then
                    local distance = (playerPos - obj.HumanoidRootPart.Position).Magnitude
                    
                    if distance < 500 then
                        print("Found Model:", obj.Name, "Distance:", math.floor(distance), "Health:", humanoid.Health)
                        foundNPCs = foundNPCs + 1
                        
                        if obj.Name == "CityNPC" then
                            print("✓ Matched CityNPC exactly!")
                            if distance < shortestDistance then
                                shortestDistance = distance
                                nearestNPC = obj
                            end
                        elseif obj.Name:find("CityNPC") then
                            print("✓ Matched CityNPC pattern!")
                            if distance < shortestDistance then
                                shortestDistance = distance
                                nearestNPC = obj
                            end
                        elseif obj.Name:find("City") then
                            print("✓ Matched City pattern!")
                            if distance < shortestDistance then
                                shortestDistance = distance
                                nearestNPC = obj
                            end
                        else
                            print("✗ No match for:", obj.Name)
                        end
                    end
                end
            end
        end
    end
    
    print("Total NPCs found in 500m:", foundNPCs)
    if nearestNPC then
        print("Selected NPC:", nearestNPC.Name, "Distance:", math.floor(shortestDistance))
    else
        print("No valid NPC selected")
    end
    print("=== END DEBUG ===")
    
    return nearestNPC
end

local function teleportToNPC(npc)
    if not player.Character or not player.Character:FindFirstChild("HumanoidRootPart") then
        return false
    end
    
    if not npc or not npc:FindFirstChild("HumanoidRootPart") then
        return false
    end
    
    local rootPart = player.Character.HumanoidRootPart
    local humanoid = player.Character.Humanoid
    
    local initialDistance = (rootPart.Position - npc.HumanoidRootPart.Position).Magnitude
    if initialDistance > 100 then
        return false
    end
    
    local npcPos = npc.HumanoidRootPart.Position
    if math.abs(npcPos.X) > 10000 or math.abs(npcPos.Z) > 10000 or npcPos.Y < -1000 or npcPos.Y > 1000 then
        return false
    end
    
    for _, part in pairs(player.Character:GetChildren()) do
        if part:IsA("BasePart") then
            part.CanCollide = false
        end
    end
    
    for _, obj in pairs(rootPart:GetChildren()) do
        if obj:IsA("BodyVelocity") or obj:IsA("BodyPosition") or obj:IsA("BodyAngularVelocity") then
            obj:Destroy()
        end
    end
    
    humanoid.PlatformStand = true
    
    local npcPos = npc.HumanoidRootPart.Position
    local targetPos = Vector3.new(npcPos.X, npcPos.Y + 3, npcPos.Z)
    
    local bodyPosition = Instance.new("BodyPosition")
    bodyPosition.MaxForce = Vector3.new(math.huge, math.huge, math.huge)
    bodyPosition.Position = targetPos
    bodyPosition.D = 3000
    bodyPosition.P = 12000
    bodyPosition.Parent = rootPart
    
    local bodyAngularVelocity = Instance.new("BodyAngularVelocity")
    bodyAngularVelocity.MaxTorque = Vector3.new(math.huge, math.huge, math.huge)
    bodyAngularVelocity.AngularVelocity = Vector3.new(0, 0, 0)
    bodyAngularVelocity.Parent = rootPart
    
    spawn(function()
        local maxFlyTime = 10
        local startTime = tick()
        local stuckCheckTime = tick()
        local lastPos = rootPart.Position
        
        while autoFarmEnabled and player.Character and player.Character:FindFirstChild("HumanoidRootPart") do
            local currentTime = tick()
            
            if currentTime - startTime > maxFlyTime then
                break
            end
            
            if not npc or not npc.Parent or not npc:FindFirstChild("HumanoidRootPart") then
                break
            end
            
            local currentPos = player.Character.HumanoidRootPart.Position
            
            if math.abs(currentPos.X) > 8000 or math.abs(currentPos.Z) > 8000 or currentPos.Y < -500 or currentPos.Y > 800 then
                break
            end
            
            if currentTime - stuckCheckTime > 2 then
                local moveDistance = (currentPos - lastPos).Magnitude
                if moveDistance < 5 then
                    break
                end
                lastPos = currentPos
                stuckCheckTime = currentTime
            end
            
            local npcCurrentPos = npc.HumanoidRootPart.Position
            local distanceToNPC = (currentPos - npcCurrentPos).Magnitude
            
            if distanceToNPC > 150 then
                break
            end
            
            local newTargetPos = npcCurrentPos + Vector3.new(0, 3, 0)
            local distanceToTarget = (currentPos - newTargetPos).Magnitude
            
            if bodyPosition and bodyPosition.Parent then
                bodyPosition.Position = newTargetPos
            end
            
            if distanceToTarget < 0.5 then
                break
            end
            
            if player.Character:FindFirstChild("HumanoidRootPart") then
                local currentPos = player.Character.HumanoidRootPart.Position
                local lookDirection = (npcCurrentPos - currentPos).Unit
                local tiltedCFrame = CFrame.new(currentPos, currentPos + lookDirection) * CFrame.Angles(math.rad(-90), 0, 0)
                player.Character.HumanoidRootPart.CFrame = tiltedCFrame
            end
            
            wait(0.1)
        end
    end)
    
    lastPosition = targetPos
    lastPositionTime = tick()
    
    return true
end

local function bypassNetworkDetection()
    pcall(function()
        local mt = getrawmetatable(game)
        if not mt then return end
        
        local oldNamecall = mt.__namecall
        local oldIndex = mt.__index
        local oldNewIndex = mt.__newindex
        
        setreadonly(mt, false)
        
        mt.__namecall = function(self, ...)
            local method = getnamecallmethod()
            local args = {...}
            
            if method == "FireServer" and self.Name == "RemoteEvent" then
                if string.find(tostring(self), "Anti") or string.find(tostring(self), "Detect") or string.find(tostring(self), "Check") then
                    return
                end
            end
            
            if method == "InvokeServer" and self.Name == "RemoteFunction" then
                if string.find(tostring(self), "Anti") or string.find(tostring(self), "Detect") or string.find(tostring(self), "Check") then
                    return
                end
            end
            
            return oldNamecall(self, ...)
        end
        
        mt.__newindex = function(t, k, v)
            if k == "CFrame" and typeof(v) == "CFrame" then
                if t == player.Character.HumanoidRootPart then
                    local currentPos = t.Position
                    local newPos = v.Position
                    local distance = (newPos - currentPos).Magnitude
                    
                    if distance > maxTeleportDistance then
                        return
                    end
                end
            end
            
            return oldNewIndex(t, k, v)
        end
        
        setreadonly(mt, true)
    end)
end

local function startFakeHeartbeat()
    spawn(function()
        while autoFarmEnabled do
            if player.Character and player.Character:FindFirstChild("Humanoid") then
                local humanoid = player.Character.Humanoid
                
                humanoid.WalkSpeed = originalWalkSpeed
                humanoid.JumpPower = 50
                
                local fakeMovement = Vector3.new(
                    math.random(-1, 1) * 0.1,
                    0,
                    math.random(-1, 1) * 0.1
                )
                
                if player.Character.HumanoidRootPart then
                    local currentCF = player.Character.HumanoidRootPart.CFrame
                    player.Character.HumanoidRootPart.CFrame = currentCF + fakeMovement
                end
            end
            
            wait(0.5)
        end
    end)
end

local function startAutoFarm()
    if autoFarmConnection then
        autoFarmConnection:Disconnect()
    end
    
    bypassNetworkDetection()
    
    autoFarmConnection = spawn(function()
        while autoFarmEnabled do
            enableNoclip()
            
            if not currentTargetNPC or not currentTargetNPC.Parent or not currentTargetNPC:FindFirstChild("Humanoid") or currentTargetNPC.Humanoid.Health <= 0 then
                currentTargetNPC = findNearestNPC()
                
                if currentTargetNPC then
                    local distance = math.floor((player.Character.HumanoidRootPart.Position - currentTargetNPC.HumanoidRootPart.Position).Magnitude)
                    farmStatusLabel.Text = "Target: " .. currentTargetNPC.Name .. " (" .. distance .. "m)"
                    
                    local timeSinceLastTeleport = tick() - lastPositionTime
                    if timeSinceLastTeleport >= teleportCooldown then
                        teleportToNPC(currentTargetNPC)
                    else
                        wait(teleportCooldown - timeSinceLastTeleport)
                        teleportToNPC(currentTargetNPC)
                    end
                else
                    farmStatusLabel.Text = "Status: Không tìm thấy NPC trong 500m"
                end
            else
                if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
                    local npcPosition = currentTargetNPC.HumanoidRootPart.Position
                    local targetPosition = npcPosition + Vector3.new(math.random(-2, 2), farmDistance, math.random(-2, 2))
                    local currentDistance = math.floor((player.Character.HumanoidRootPart.Position - npcPosition).Magnitude)
                    
                    if player.Character.HumanoidRootPart:FindFirstChild("BodyPosition") then
                        player.Character.HumanoidRootPart.BodyPosition.Position = targetPosition
                    else
                        local bodyPosition = Instance.new("BodyPosition")
                        bodyPosition.MaxForce = Vector3.new(math.huge, math.huge, math.huge)
                        bodyPosition.Position = targetPosition
                        bodyPosition.D = 2000
                        bodyPosition.P = 10000
                        bodyPosition.Parent = player.Character.HumanoidRootPart
                    end
                    
                    if player.Character:FindFirstChild("Humanoid") then
                        player.Character.Humanoid.PlatformStand = true
                    end
                    
                    farmStatusLabel.Text = "Farming: " .. currentTargetNPC.Name .. " (" .. currentDistance .. "m)"
                end
                
                if not autoAttackEnabled then
                    autoAttackEnabled = true
                    startAutoAttack()
                end
            end
            
            wait(1.5)
        end
    end)
end

local function stopAutoFarm()
    autoFarmEnabled = false
    currentTargetNPC = nil
    
    if autoFarmConnection then
        autoFarmConnection:Disconnect()
        autoFarmConnection = nil
    end
    
    disableNoclip()
    
    if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
        if player.Character.HumanoidRootPart:FindFirstChild("BodyPosition") then
            player.Character.HumanoidRootPart.BodyPosition:Destroy()
        end
        if player.Character.HumanoidRootPart:FindFirstChild("BodyVelocity") then
            player.Character.HumanoidRootPart.BodyVelocity:Destroy()
        end
        if player.Character:FindFirstChild("Humanoid") then
            player.Character.Humanoid.PlatformStand = false
        end
    end
    
    if autoAttackEnabled then
        autoAttackEnabled = false
        autoAttackToggle.Text = "OFF"
        autoAttackToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        autoAttackToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
        }
        
        autoToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        local tween = TweenService:Create(autoToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 2, 0, 2)}
        )
        tween:Play()
        
        autoAttackGUIVisible = false
        autoAttackGUI.Visible = false
        stopAutoAttack()
    end
    
    farmStatusLabel.Text = "Status: Đã dừng"
end

local function toggleAutoFarm()
    autoFarmEnabled = not autoFarmEnabled
    
    if autoFarmEnabled then
        autoFarmToggle.Text = "ON"
        autoFarmToggle.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        autoFarmToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(0, 200, 80)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(0, 150, 60))
        }
        
        farmToggleContainer.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        local tween = TweenService:Create(farmToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 42, 0, 2)}
        )
        tween:Play()
        
        autoFarmGUIVisible = true
        autoFarmGUI.Visible = true
        startAutoFarm()
        statusLabel.Text = "Auto Farm: ON"
    else
        autoFarmToggle.Text = "OFF"
        autoFarmToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        autoFarmToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
        }
        
        farmToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        local tween = TweenService:Create(farmToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 2, 0, 2)}
        )
        tween:Play()
        
        autoFarmGUIVisible = false
        autoFarmGUI.Visible = false
        stopAutoFarm()
        statusLabel.Text = "Auto Farm: OFF"
    end
end

local function toggleAutoFarmGUI()
    autoFarmEnabled = not autoFarmEnabled
    
    if autoFarmEnabled then
        farmToggleContainer.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        local tween = TweenService:Create(farmToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 42, 0, 2)}
        )
        tween:Play()
        startAutoFarm()
    else
        farmToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        local tween = TweenService:Create(farmToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 2, 0, 2)}
        )
        tween:Play()
        stopAutoFarm()
    end
end

local function sendMessage(message)
    pcall(function()
        local success = false
        local textChatService = game:GetService("TextChatService")
        if textChatService then
            local textChannels = textChatService:FindFirstChild("TextChannels")
            if textChannels then
                local generalChannel = textChannels:FindFirstChild("RBXGeneral")
                if generalChannel and generalChannel.SendAsync then
                    generalChannel:SendAsync(message)
                    success = true
                end
            end
        end
        
        if not success then
            local chatRemote = ReplicatedStorage:FindFirstChild("DefaultChatSystemChatEvents")
            if chatRemote then
                local sayMessageRequest = chatRemote:FindFirstChild("SayMessageRequest")
                if sayMessageRequest then
                    sayMessageRequest:FireServer(message, "All")
                end
            end
        end
    end)
end

local function startChatWar()
    if chatWarConnection then
        chatWarConnection:Disconnect()
    end
    
    chatWarConnection = spawn(function()
        local index = 1
        local delay = tonumber(chatDelayBox.Text) or 1
        if delay < 0.5 then delay = 0.5 end
        
        while chatWarEnabled do
            if #chat > 0 then
                local message = chat[index]
                if message and message ~= "" then
                    sendMessage(message)
                end
                index = index + 1
                if index > #chat then
                    index = 1
                end
            end
            wait(delay)
        end
    end)
end

local function stopChatWar()
    if chatWarConnection then
        chatWarConnection:Disconnect()
        chatWarConnection = nil
    end
end

local function startSpinAround()
    if spinAroundConnection then
        spinAroundConnection:Disconnect()
    end
    
    spinAroundConnection = RunService.RenderStepped:Connect(function()
        if spinAroundEnabled and player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
            local rootPart = player.Character.HumanoidRootPart
            rootPart.CFrame = rootPart.CFrame * CFrame.Angles(0, math.rad(35), 0)
        end
    end)
end

local function stopSpinAround()
    if spinAroundConnection then
        spinAroundConnection:Disconnect()
        spinAroundConnection = nil
    end
end

local function toggleAutoHeal()
    spinAroundEnabled = not spinAroundEnabled
    
    if spinAroundEnabled then
        autoHealToggle.Text = "ON"
        autoHealToggle.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        autoHealToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(0, 200, 80)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(0, 150, 60))
        }
        startSpinAround()
        statusLabel.Text = "Quay Tròn: ON"
    else
        autoHealToggle.Text = "OFF"
        autoHealToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        autoHealToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
        }
        stopSpinAround()
        statusLabel.Text = "Quay Tròn: OFF"
    end
end

local function scanAllUIElements()
    local uiInfo = ""
    local elementCount = 0
    
    uiInfo = uiInfo .. "=== SCAN TẤT CẢ UI ELEMENTS ===\n\n"
    
    for _, gui in pairs(playerGui:GetChildren()) do
        if gui:IsA("ScreenGui") then
            uiInfo = uiInfo .. "ScreenGui: " .. gui.Name .. "\n"
            
            for _, element in pairs(gui:GetDescendants()) do
                elementCount = elementCount + 1
                
                if element:IsA("Frame") then
                    uiInfo = uiInfo .. "  Frame: " .. element.Name
                    if element.Visible then uiInfo = uiInfo .. " (Visible)" end
                    uiInfo = uiInfo .. "\n"
                    
                elseif element:IsA("TextButton") then
                    uiInfo = uiInfo .. "  TextButton: " .. element.Name
                    if element.Text and element.Text ~= "" then
                        uiInfo = uiInfo .. " [" .. element.Text .. "]"
                    end
                    if element.Visible then uiInfo = uiInfo .. " (Visible)" end
                    uiInfo = uiInfo .. "\n"
                    
                elseif element:IsA("ImageButton") then
                    uiInfo = uiInfo .. "  ImageButton: " .. element.Name
                    if element.Visible then uiInfo = uiInfo .. " (Visible)" end
                    uiInfo = uiInfo .. "\n"
                    
                elseif element:IsA("TextLabel") then
                    uiInfo = uiInfo .. "  TextLabel: " .. element.Name
                    if element.Text and element.Text ~= "" and not element.Text:find("TextLabel") then
                        uiInfo = uiInfo .. " [" .. element.Text .. "]"
                    end
                    if element.Visible then uiInfo = uiInfo .. " (Visible)" end
                    uiInfo = uiInfo .. "\n"
                    
                elseif element:IsA("TextBox") then
                    uiInfo = uiInfo .. "  TextBox: " .. element.Name
                    if element.Text and element.Text ~= "" then
                        uiInfo = uiInfo .. " [" .. element.Text .. "]"
                    end
                    if element.Visible then uiInfo = uiInfo .. " (Visible)" end
                    uiInfo = uiInfo .. "\n"
                    
                elseif element:IsA("ImageLabel") then
                    uiInfo = uiInfo .. "  ImageLabel: " .. element.Name
                    if element.Visible then uiInfo = uiInfo .. " (Visible)" end
                    uiInfo = uiInfo .. "\n"
                end
            end
            uiInfo = uiInfo .. "\n"
        end
    end
    
    for _, item in pairs(player.Backpack:GetChildren()) do
        if item:IsA("Tool") then
            uiInfo = uiInfo .. "Backpack Item: " .. item.Name .. "\n"
        end
    end
    
    if player.Character then
        for _, item in pairs(player.Character:GetChildren()) do
            if item:IsA("Tool") then
                uiInfo = uiInfo .. "Equipped Item: " .. item.Name .. "\n"
            end
        end
    end
    
    uiInfo = uiInfo .. "\nTổng cộng: " .. elementCount .. " UI elements\n"
    uiInfo = uiInfo .. "Thời gian scan: " .. os.date("%H:%M:%S")
    
    return uiInfo
end

local function updateDebugDisplay()
    if not debugEnabled or not debugTextLabel then return end
    
    local uiInfo = scanAllUIElements()
    debugTextLabel.Text = uiInfo
    
    local textSize = debugTextLabel.TextBounds.Y
    debugTextLabel.Size = UDim2.new(1, -10, 0, math.max(textSize + 50, 400))
    debugScrollFrame.CanvasSize = UDim2.new(0, 0, 0, textSize + 100)
end

local function startDebugSystem()
    if debugConnection then
        debugConnection:Disconnect()
    end
    
    debugConnection = spawn(function()
        while debugEnabled do
            updateDebugDisplay()
            wait(2)
        end
    end)
end

local function stopDebugSystem()
    if debugConnection then
        debugConnection:Disconnect()
        debugConnection = nil
    end
end

local function toggleDebugUI()
    debugEnabled = not debugEnabled
    
    if debugEnabled then
        debugToggle.Text = "ON"
        debugToggle.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        debugToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(0, 200, 80)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(0, 150, 60))
        }
        debugDisplay.Visible = true
        startDebugSystem()
        statusLabel.Text = "Debug UI: ON - Scanning UI Elements"
    else
        debugToggle.Text = "OFF"
        debugToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        debugToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
        }
        debugDisplay.Visible = false
        stopDebugSystem()
        statusLabel.Text = "Debug UI: OFF"
    end
end

local function toggleChatWar()
    chatWarEnabled = not chatWarEnabled
    
    if chatWarEnabled then
        chatWarToggle.Text = "ON"
        chatWarToggle.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        chatWarToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(0, 200, 80)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(0, 150, 60))
        }
        
        chatToggleContainer.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        local tween = TweenService:Create(chatToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 42, 0, 2)}
        )
        tween:Play()
        
        chatWarGUIVisible = true
        chatWarGUI.Visible = true
        startChatWar()
        statusLabel.Text = "Chat War: ON"
    else
        chatWarToggle.Text = "OFF"
        chatWarToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        chatWarToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
        }
        
        chatToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        local tween = TweenService:Create(chatToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 2, 0, 2)}
        )
        tween:Play()
        
        chatWarGUIVisible = false
        chatWarGUI.Visible = false
        stopChatWar()
        statusLabel.Text = "Chat War: OFF"
    end
end

local function toggleChatWarGUI()
    chatWarEnabled = not chatWarEnabled
    
    if chatWarEnabled then
        chatToggleContainer.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        local tween = TweenService:Create(chatToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 42, 0, 2)}
        )
        tween:Play()
        startChatWar()
    else
        chatToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        local tween = TweenService:Create(chatToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 2, 0, 2)}
        )
        tween:Play()
        stopChatWar()
    end
end

local function updatePlayersList()
    playersList = {}
    for _, plr in pairs(Players:GetPlayers()) do
        if plr ~= player and plr.Character and plr.Character:FindFirstChild("HumanoidRootPart") then
            table.insert(playersList, plr)
        end
    end
end

local function createDropdownItems()
    for _, child in pairs(dropdownList:GetChildren()) do
        if child:IsA("TextButton") then
            child:Destroy()
        end
    end
    
    updatePlayersList()
    
    for i, plr in pairs(playersList) do
        local item = Instance.new("TextButton")
        item.Name = "PlayerItem_" .. plr.Name
        item.Parent = dropdownList
        item.Size = UDim2.new(1, -8, 0, 25)
        item.Position = UDim2.new(0, 4, 0, (i-1) * 27)
        item.BackgroundColor3 = Color3.fromRGB(40, 40, 45)
        item.BorderSizePixel = 0
        item.Text = plr.Name
        item.TextColor3 = Color3.fromRGB(255, 255, 255)
        item.TextSize = 10
        item.Font = Enum.Font.Gotham
        item.ZIndex = 21
        
        local itemCorner = Instance.new("UICorner")
        itemCorner.CornerRadius = UDim.new(0, 6)
        itemCorner.Parent = item
        
        item.MouseButton1Click:Connect(function()
            selectedTarget = plr
            targetDropdown.Text = plr.Name
            dropdownList.Visible = false
            aimbotDropdownOpen = false
        end)
        
        item.MouseEnter:Connect(function()
            item.BackgroundColor3 = Color3.fromRGB(255, 0, 100)
        end)
        
        item.MouseLeave:Connect(function()
            item.BackgroundColor3 = Color3.fromRGB(40, 40, 45)
        end)
    end
    
    dropdownList.CanvasSize = UDim2.new(0, 0, 0, #playersList * 27)
end

local function isTargetInFOV()
    if not selectedTarget or not selectedTarget.Character or not selectedTarget.Character:FindFirstChild("Head") then
        return false
    end
    
    local success, result = pcall(function()
        local targetPos = selectedTarget.Character.Head.Position
        local screenPos, onScreen = camera:WorldToScreenPoint(targetPos)
        
        if not onScreen then return false end
        
        local centerX = camera.ViewportSize.X / 2
        local centerY = camera.ViewportSize.Y / 2
        local distance = math.sqrt((screenPos.X - centerX)^2 + (screenPos.Y - centerY)^2)
        
        return distance <= fovSize
    end)
    
    return success and result
end

local function aimAtTarget()
    if not selectedTarget or not selectedTarget.Character or not selectedTarget.Character:FindFirstChild("Head") then
        return
    end
    
    if not player.Character or not player.Character:FindFirstChild("HumanoidRootPart") then
        return
    end
    
    if not isTargetInFOV() then
        return
    end
    
    pcall(function()
        local targetPosition = selectedTarget.Character.Head.Position
        local currentCamera = workspace.CurrentCamera
        currentCamera.CFrame = CFrame.lookAt(currentCamera.CFrame.Position, targetPosition)
    end)
end

local function startAimbot()
    if aimbotConnection then
        aimbotConnection:Disconnect()
    end
    
    aimbotConnection = RunService.RenderStepped:Connect(function()
        if aimbotEnabled and selectedTarget then
            aimAtTarget()
        end
    end)
end

local function stopAimbot()
    if aimbotConnection then
        aimbotConnection:Disconnect()
        aimbotConnection = nil
    end
end

local function updateFOVSize(value)
    fovSize = math.floor(value * 200 + 50)
    fovLabel.Text = "FOV: " .. fovSize
    if fovCircle then
        fovCircle.Size = UDim2.new(0, fovSize * 2, 0, fovSize * 2)
        fovCircle.Position = UDim2.new(0.5, -fovSize, 0.5, -fovSize)
    end
end

local function makeFOVSliderDraggable()
    local dragging = false
    
    fovSlider.InputBegan:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.MouseButton1 then
            dragging = true
        end
    end)
    
    UserInputService.InputEnded:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.MouseButton1 then
            dragging = false
        end
    end)
    
    UserInputService.InputChanged:Connect(function(input)
        if dragging and input.UserInputType == Enum.UserInputType.MouseMovement then
            local mousePos = UserInputService:GetMouseLocation()
            local sliderPos = fovSlider.AbsolutePosition
            local sliderSize = fovSlider.AbsoluteSize
            
            local relativeX = math.clamp((mousePos.X - sliderPos.X) / sliderSize.X, 0, 1)
            
            fovSliderBall.Position = UDim2.new(relativeX, -8, 0, -5)
            updateFOVSize(relativeX)
        end
    end)
end

local function toggleAimbot()
    aimbotEnabled = not aimbotEnabled
    
    if aimbotEnabled then
        aimbotToggle.Text = "ON"
        aimbotToggle.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        aimbotToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(0, 200, 80)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(0, 150, 60))
        }
        
        aimbotToggleContainer.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        local tween = TweenService:Create(aimbotToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 42, 0, 2)}
        )
        tween:Play()
        
        aimbotGUIVisible = true
        aimbotGUI.Visible = true
        createFOVCircle()
        if fovCircle then fovCircle.Visible = true end
        startAimbot()
        statusLabel.Text = "Aimbot: ON"
    else
        aimbotToggle.Text = "OFF"
        aimbotToggle.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        aimbotToggleGradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 70, 70)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 40))
        }
        
        aimbotToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        local tween = TweenService:Create(aimbotToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 2, 0, 2)}
        )
        tween:Play()
        
        aimbotGUIVisible = false
        aimbotGUI.Visible = false
        if fovCircle then fovCircle.Visible = false end
        stopAimbot()
        statusLabel.Text = "Aimbot: OFF"
    end
end

local function toggleAimbotGUI()
    aimbotEnabled = not aimbotEnabled
    
    if aimbotEnabled then
        aimbotToggleContainer.BackgroundColor3 = Color3.fromRGB(0, 180, 60)
        local tween = TweenService:Create(aimbotToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 42, 0, 2)}
        )
        tween:Play()
        createFOVCircle()
        if fovCircle then fovCircle.Visible = true end
        startAimbot()
    else
        aimbotToggleContainer.BackgroundColor3 = Color3.fromRGB(220, 50, 50)
        local tween = TweenService:Create(aimbotToggleBall, 
            TweenInfo.new(0.3, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), 
            {Position = UDim2.new(0, 2, 0, 2)}
        )
        tween:Play()
        if fovCircle then fovCircle.Visible = false end
        stopAimbot()
    end
end

local function showMenu()
    if menuOpen then return end
    menuOpen = true
    mainFrame.Visible = true
    
    mainFrame.Size = UDim2.new(0, 0, 0, 0)
    local tween = TweenService:Create(mainFrame, 
        TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), 
        {Size = UDim2.new(0, 340, 0, 285)}
    )
    tween:Play()
end

local function hideMenu()
    if not menuOpen then return end
    menuOpen = false
    
    local tween = TweenService:Create(mainFrame, 
        TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.In), 
        {Size = UDim2.new(0, 0, 0, 0)}
    )
    tween:Play()
    
    tween.Completed:Connect(function()
        mainFrame.Visible = false
    end)
end

local function makeDraggable(frame)
    local dragging = false
    local dragStart = nil
    local startPos = nil
    local dragConnection = nil
    local inputConnection = nil
    
    frame.InputBegan:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then
            dragging = true
            dragStart = input.Position
            startPos = frame.Position
            
            dragConnection = UserInputService.InputChanged:Connect(function(input2)
                if input2.UserInputType == Enum.UserInputType.MouseMovement or input2.UserInputType == Enum.UserInputType.Touch then
                    if dragging then
                        local delta = input2.Position - dragStart
                        frame.Position = UDim2.new(startPos.X.Scale, startPos.X.Offset + delta.X, startPos.Y.Scale, startPos.Y.Offset + delta.Y)
                    end
                end
            end)
            
            inputConnection = UserInputService.InputEnded:Connect(function(input2)
                if input2.UserInputType == Enum.UserInputType.MouseButton1 or input2.UserInputType == Enum.UserInputType.Touch then
                    dragging = false
                    if dragConnection then
                        dragConnection:Disconnect()
                        dragConnection = nil
                    end
                    if inputConnection then
                        inputConnection:Disconnect()
                        inputConnection = nil
                    end
                end
            end)
        end
    end)
end

makeDraggable(logoButton)
makeDraggable(mainFrame)
makeDraggable(autoAttackGUI)
makeDraggable(chatWarGUI)
makeDraggable(debugDisplay)
makeDraggable(aimbotGUI)
makeDraggable(autoJumpGUI)
makeDraggable(speedHackGUI)
makeDraggable(autoFarmGUI)

logoButton.MouseButton1Click:Connect(function()
    if not isDragging then
        showMenu()
    end
end)

closeButton.MouseButton1Click:Connect(hideMenu)
espToggle.MouseButton1Click:Connect(toggleESP)
autoAttackToggle.MouseButton1Click:Connect(toggleAutoAttack)
autoToggleButton.MouseButton1Click:Connect(toggleAutoAttackGUI)
chatWarToggle.MouseButton1Click:Connect(toggleChatWar)
chatToggleButton.MouseButton1Click:Connect(toggleChatWarGUI)
speedToggle.MouseButton1Click:Connect(toggleSpeedHack)
speedHackToggleButton.MouseButton1Click:Connect(toggleSpeedHackGUI)
debugToggle.MouseButton1Click:Connect(toggleDebugUI)
autoFarmToggle.MouseButton1Click:Connect(toggleAutoFarm)
farmToggleButton.MouseButton1Click:Connect(toggleAutoFarmGUI)
autoHealToggle.MouseButton1Click:Connect(toggleAutoHeal)
jumpToggle.MouseButton1Click:Connect(toggleAutoJump)
jumpToggleButton.MouseButton1Click:Connect(toggleAutoJumpGUI)
aimbotToggle.MouseButton1Click:Connect(toggleAimbot)
aimbotToggleButton.MouseButton1Click:Connect(toggleAimbotGUI)

targetDropdown.MouseButton1Click:Connect(function()
    aimbotDropdownOpen = not aimbotDropdownOpen
    if aimbotDropdownOpen then
        createDropdownItems()
        dropdownList.Size = UDim2.new(0, 160, 0, math.min(#playersList * 27, 100))
        dropdownList.Visible = true
    else
        dropdownList.Visible = false
    end
end)

refreshButton.MouseButton1Click:Connect(function()
    createDropdownItems()
    targetDropdown.Text = "Chọn mục tiêu"
    selectedTarget = nil
end)

makeFOVSliderDraggable()
updatePlayersList()
createFOVCircle()

chatDelayBox.FocusLost:Connect(function()
    local value = tonumber(chatDelayBox.Text)
    if not value or value < 0.5 then
        chatDelayBox.Text = "0.5"
    end
end)

speedInputBox.FocusLost:Connect(function()
    local value = tonumber(speedInputBox.Text)
    if not value or value < 1.0 then
        speedInputBox.Text = "1.0"
    elseif value > 10.0 then
        speedInputBox.Text = "10.0"
    end
end)

player.CharacterAdded:Connect(function(character)
    character:WaitForChild("Humanoid")
    wait(1)
    originalWalkSpeed = character.Humanoid.WalkSpeed
end)

if player.Character and player.Character:FindFirstChild("Humanoid") then
    originalWalkSpeed = player.Character.Humanoid.WalkSpeed
end

RunService.Heartbeat:Connect(updateESP)

spawn(function()
    while true do
        if espEnabled then
            scanForCharacters()
        end
        wait(2)
    end
end)