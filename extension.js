const vscode = require('vscode');
const { spawn, exec } = require('child_process');
const path = require('path');
const http = require('http');

let statusBarItem;
let companionProcess = null;

function getPairingUrl() {
    return 'https://mocha-judo-powdery.ngrok-free.dev/?token=agy_remote_secure_key';
}

function checkCompanionStatus(callback) {
    const req = http.get('http://127.0.0.1:8765/api/companion/mode', { timeout: 1000 }, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
            try {
                const parsed = JSON.parse(data);
                callback(parsed.mode || 'active');
            } catch (e) {
                callback('active');
            }
        });
    });
    req.on('error', () => callback('offline'));
    req.on('timeout', () => { req.destroy(); callback('offline'); });
}

function updateStatusBar(mode) {
    if (!statusBarItem) return;
    if (mode === 'active') {
        statusBarItem.text = '$(device-mobile) Companion: Online';
        statusBarItem.tooltip = 'Antigravity Mobile Companion is ACTIVE.\nClick for controls.';
        statusBarItem.backgroundColor = undefined;
    } else if (mode === 'standby') {
        statusBarItem.text = '$(device-mobile) Companion: Standby';
        statusBarItem.tooltip = 'Antigravity Mobile Companion is in STANDBY.\nClick for controls.';
        statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
    } else {
        statusBarItem.text = '$(device-mobile) Companion: Offline';
        statusBarItem.tooltip = 'Antigravity Mobile Companion is OFFLINE.\nClick to start.';
        statusBarItem.backgroundColor = undefined;
    }
}

function activate(context) {
    // 1. Create Status Bar Item
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'antigravity.companion.menu';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    // Initial check
    checkCompanionStatus(mode => updateStatusBar(mode));
    const interval = setInterval(() => checkCompanionStatus(mode => updateStatusBar(mode)), 5000);
    context.subscriptions.push({ dispose: () => clearInterval(interval) });

    // 2. Command: Menu
    const menuCmd = vscode.commands.registerCommand('antigravity.companion.menu', async () => {
        const items = [
            { label: '$(play) Start Companion Mode', description: 'Enable mobile control with desktop parity', action: 'start' },
            { label: '$(debug-pause) Put into Standby', description: 'Revert desktop permissions while keeping tunnel awake', action: 'standby' },
            { label: '$(device-mobile) Show Pairing URL', description: 'Display remote and local connection links', action: 'showQR' },
            { label: '$(globe) Open Mobile App in Browser', description: 'Launch PWA interface in your default browser', action: 'openPWA' }
        ];
        const selection = await vscode.window.showQuickPick(items, { placeHolder: 'Antigravity Mobile Companion Controls' });
        if (!selection) return;

        if (selection.action === 'start') {
            vscode.commands.executeCommand('antigravity.companion.start');
        } else if (selection.action === 'standby') {
            vscode.commands.executeCommand('antigravity.companion.standby');
        } else if (selection.action === 'showQR') {
            vscode.commands.executeCommand('antigravity.companion.showQR');
        } else if (selection.action === 'openPWA') {
            vscode.commands.executeCommand('antigravity.companion.openPWA');
        }
    });

    // 3. Command: Start
    const startCmd = vscode.commands.registerCommand('antigravity.companion.start', () => {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || context.extensionPath;
        const terminal = vscode.window.createTerminal({ name: 'Antigravity Companion', cwd: workspaceRoot });
        terminal.sendText('python run_companion.py');
        vscode.window.showInformationMessage('Starting Antigravity Mobile Companion daemon...');
        setTimeout(() => checkCompanionStatus(mode => updateStatusBar(mode)), 3000);
    });

    // 4. Command: Standby
    const standbyCmd = vscode.commands.registerCommand('antigravity.companion.standby', () => {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || context.extensionPath;
        exec('python shutdown_companion.py', { cwd: workspaceRoot }, (err, stdout) => {
            if (err) {
                vscode.window.showErrorMessage(`Failed to enter Standby: ${err.message}`);
            } else {
                vscode.window.showInformationMessage('Companion Mode is now in Standby.');
                updateStatusBar('standby');
            }
        });
    });

    // 5. Command: Show URL
    const showQRCmd = vscode.commands.registerCommand('antigravity.companion.showQR', async () => {
        const url = getPairingUrl();
        const action = await vscode.window.showInformationMessage(
            `📱 Mobile Companion URL:\n${url}`,
            'Open in Browser',
            'Copy URL'
        );
        if (action === 'Open in Browser') {
            vscode.env.openExternal(vscode.Uri.parse(url));
        } else if (action === 'Copy URL') {
            await vscode.env.clipboard.writeText(url);
            vscode.window.showInformationMessage('Pairing URL copied to clipboard!');
        }
    });

    // 6. Command: Open PWA
    const openPWACmd = vscode.commands.registerCommand('antigravity.companion.openPWA', () => {
        vscode.env.openExternal(vscode.Uri.parse(getPairingUrl()));
    });

    context.subscriptions.push(menuCmd, startCmd, standbyCmd, showQRCmd, openPWACmd);
}

function deactivate() {
    if (statusBarItem) {
        statusBarItem.dispose();
    }
}

module.exports = {
    activate,
    deactivate
};
