% PSF and Quality Factor (Q) Effect on Detector Sampling
% Demonstrates diffraction-limited vs pixel-limited imaging

clear; clc;

%% System Parameters
lambda = 550e-9;          % Wavelength [m]
D = 0.1;                  % Aperture diameter [m]
f_l = 1.0;                % Effective focal length [m]
H = 500e3;                % Orbit altitude [m]
grid_size = 256;

% Quality factors to compare
Q_vals = [0.5, 1.0, 2.0]; % diffraction-limited -> pixel-limited

%% Diffraction PSF parameters
k = 2*pi/lambda;
airy_diam = 2.44 * lambda * f_l / D;   % Airy disk diameter (PSF)

%% Spatial grid (high-resolution reference grid)
dx = airy_diam / 40;
x = (-grid_size/2:grid_size/2-1) * dx;
[X,Y] = meshgrid(x);
r = sqrt(X.^2 + Y.^2);

% Airy PSF
R = (pi*D/lambda/f_l) * r;
PSF = (2*besselj(1,R)./R).^2;
PSF(r==0) = 1;
PSF = PSF / max(PSF(:));

%% Plot PSF with pixel sampling for different Q
figure;
tiledlayout(1,length(Q_vals),"Padding","compact");

for i = 1:length(Q_vals)
    Q = Q_vals(i);

    % Pixel size from empirical relation
    p = 2.44 * (lambda * f_l / H) * Q;

    nexttile;
    imagesc(x*1e6, x*1e6, PSF);
    colormap hot; axis image; hold on;

    % Overlay pixel grid
    px = -airy_diam: p : airy_diam;
    for kx = px
        plot([kx kx]*1e6, [-airy_diam airy_diam]*1e6, 'c');
        plot([-airy_diam airy_diam]*1e6, [kx kx]*1e6, 'c');
    end

    title(sprintf('Q = %.1f  |  p / PSF = %.1f', Q, Q));
    xlabel('\mum'); ylabel('\mum');
end

sgtitle('Effect of Quality Factor (Q) on PSF Sampling');