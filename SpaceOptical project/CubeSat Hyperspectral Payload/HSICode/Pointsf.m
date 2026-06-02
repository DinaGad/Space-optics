% CubeSat HSI: Fast and Correct Q–PSF–MTF–GSD Analysis

clear; clc;

%% System Parameters
lambda = 550e-9;      % Wavelength [m]
D = 0.1;              % Aperture diameter [m]
f_l = 1.0;            % Focal length [m]
H = 500e3;            % Orbit altitude [m]

Q_vals = [0.5 1.0 2.0];
grid_size = 256;

%% Diffraction PSF
airy_diam = 2.44 * lambda * f_l / D;   % Airy disk diameter
dx = airy_diam / 20;

x = (-grid_size/2:grid_size/2-1) * dx;
[X,Y] = meshgrid(x);
r = sqrt(X.^2 + Y.^2);

R = (pi*D/(lambda*f_l)) * r;
PSF = (2*besselj(1,R)./R).^2;
PSF(r==0) = 1;
PSF = PSF / max(PSF(:));

%% Preallocate
GSD = zeros(size(Q_vals));
MTF_sys = zeros(size(Q_vals));

%% --- PSF Sampling Visualization ---
figure;
tiledlayout(1,length(Q_vals),'Padding','compact');

for i = 1:length(Q_vals)
    Q = Q_vals(i);

    %  Correct pixel size definition
    p = Q * airy_diam;

    % Ground Sample Distance
    GSD(i) = H * p / f_l;

    % MTF calculations
    f_nyq = 1/(2*p);
    f_cut = D/(lambda*f_l);

    MTF_det = abs(sinc(f_nyq*p));
    MTF_opt = max(0,1 - f_nyq/f_cut);
    MTF_sys(i) = MTF_opt * MTF_det;

    % Plot PSF
    nexttile;
    imagesc(x*1e6, x*1e6, PSF);
    axis image; colormap hot; hold on;

    % Pixel grid (limited extent)
    px = -2*airy_diam : p : 2*airy_diam;
    px = px * 1e6;

    plot([px; px], repmat([-2 2]*airy_diam*1e6, length(px),1)', 'c');
    plot(repmat([-2 2]*airy_diam*1e6, length(px),1)', [px; px], 'c');

    title(sprintf('Q = %.1f',Q));
    xlabel('\mum'); ylabel('\mum');

    drawnow limitrate
end
sgtitle('PSF Sampling vs Quality Factor (Q)');

%% --- MTF vs Q ---
figure;
plot(Q_vals, MTF_sys, '-o','LineWidth',1.8);
xlabel('Quality Factor, Q','Interpreter','latex');
ylabel('System MTF (Nyquist)','Interpreter','latex');
grid on;

%% --- GSD vs Q ---
figure;
plot(Q_vals, GSD, '-s','LineWidth',1.8);
xlabel('Quality Factor, Q','Interpreter','latex');
ylabel('Ground Sample Distance (m)','Interpreter','latex');
grid on;