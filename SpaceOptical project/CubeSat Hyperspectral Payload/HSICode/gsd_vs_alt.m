% This program plots the ground sampling distance (GSD) of HSI
% against altitude using different line styles, markers, and colors.

% Define altitude range (in meters)
altitude = [300, 400, 500, 600, 700, 800]; 

% Define Ground Sample Distance (GSD) range (in meters)
GSD = linspace(10, 100, 100);

% Define constant of proportionality
k = 12;

% Initialize matrix to store Effective Focal Length (EFL)
EFL = zeros(length(altitude), length(GSD));

% Calculate EFL
for i = 1:length(altitude)
    for j = 1:length(GSD)
        EFL(i, j) = k * altitude(i) / GSD(j);
    end
end

% Line styles, markers, and colors
lineStyles = {'-', '--', ':', '-.', '-', '-.'};
markers    = {'<', 's', 'd', '^', 'x', '>'};

colors = [
    0.00 0.45 0.74;   % Blue
    0.85 0.33 0.10;   % Orange
    0.47 0.67 0.19;   % Green
    0.49 0.18 0.56;   % Purple
    0.93 0.69 0.13;   % Yellow
    0.30 0.30 0.30;   % Gray
];
% Define line / marker edge colors (6 × 3)
edge_colors = [
    0.00 0.00 0.00;   % Black
    0.20 0.20 0.60;   % Dark blue
    0.60 0.20 0.20;   % Dark red
    0.20 0.60 0.20;   % Dark green
    0.40 0.40 0.40;   % Dark gray
    0.10 0.10 0.10;   % Near black
];

% Plot
figure;
hold on;
for i = 1:length(altitude)
    plot(GSD, EFL(i,:), ...
        'LineStyle', lineStyles{i}, ...
        'Marker', markers{i}, ...
        'MarkerEdgeColor', edge_colors(i, :), ...
        'MarkerFaceColor', colors(i, :), ...
        'Color', colors(i,:), ...
        'LineWidth', 1.6, ...
        'MarkerSize', 7, ...
        'MarkerIndices', 1:10:length(GSD));
end

% Labels and legend
xlabel('Ground Sampling Distance (m)', 'FontSize', 13, 'Interpreter', 'latex');
ylabel('Effective Focal Length (mm)', 'FontSize', 13, 'Interpreter', 'latex');

legendStrings = compose('Altitude = %.1f km', altitude/1000);
legend(legendStrings, ...
    'Location', 'best', ...
    'Interpreter', 'latex', ...
    'NumColumns', 2);

grid on;
box on;
hold off;
