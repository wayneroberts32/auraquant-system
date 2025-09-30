const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = (env, argv) => {
  const isProduction = argv.mode === 'production';
  
  return {
    entry: {
      app: './assets/js/app.js',
      'api-service': './assets/js/api-service.js',
      'websocket-manager': './assets/js/websocket-manager.js',
      'workspace-manager': './assets/js/workspace-manager.js',
      'alert-system': './assets/js/alert-system.js',
      'capital-protection': './js/capital-protection.js'
    },
    
    output: {
      path: path.resolve(__dirname, 'build'),
      filename: 'js/[name].[contenthash].js',
      clean: true,
      publicPath: '/'
    },
    
    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: ['@babel/preset-env']
            }
          }
        },
        {
          test: /\.css$/,
          use: [
            isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
            'css-loader'
          ]
        },
        {
          test: /\.(scss|sass)$/,
          use: [
            isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
            'css-loader',
            'sass-loader'
          ]
        },
        {
          test: /\.(png|jpg|jpeg|gif|svg|ico)$/,
          type: 'asset/resource',
          generator: {
            filename: 'img/[name].[contenthash][ext]'
          }
        },
        {
          test: /\.(woff|woff2|eot|ttf|otf)$/,
          type: 'asset/resource',
          generator: {
            filename: 'fonts/[name].[contenthash][ext]'
          }
        }
      ]
    },
    
    plugins: [
      new HtmlWebpackPlugin({
        template: './index.html',
        filename: 'index.html',
        chunks: ['app'],
        inject: 'body'
      }),
      
      // Generate HTML for all pages
      ...['login', 'register', 'main-trading-dashboard', 'portfolio-dashboard', 
          'risk-panel', 'orders', 'positions', 'journal', 'screeners',
          'strategy-builder', 'hft-trading-panel', 'pnl-dashboard',
          'monitoring-dashboard', 'admin-monitoring', 'admin-users', 
          'admin-agents', 'ai-workers-panel', 'unified-dashboard',
          'auraquant'].map(page => 
        new HtmlWebpackPlugin({
          template: `./pages/${page}.html`,
          filename: `pages/${page}.html`,
          chunks: ['app'],
          inject: 'body'
        })
      ),
      
      new CopyWebpackPlugin({
        patterns: [
          { from: 'css', to: 'css' },
          { from: 'assets/img', to: 'img' },
          { from: 'Logo', to: 'Logo' },
          { from: 'pages', to: 'pages' },
          { from: '_headers', to: '_headers', noErrorOnMissing: true }
        ]
      }),
      
      ...(isProduction ? [
        new MiniCssExtractPlugin({
          filename: 'css/[name].[contenthash].css'
        })
      ] : [])
    ],
    
    optimization: {
      minimize: isProduction,
      minimizer: [
        new TerserPlugin({
          terserOptions: {
            compress: {
              drop_console: true,
              drop_debugger: true
            }
          }
        }),
        new CssMinimizerPlugin()
      ],
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            priority: -10
          },
          common: {
            minChunks: 2,
            priority: -20,
            reuseExistingChunk: true
          }
        }
      }
    },
    
    devServer: {
      static: {
        directory: path.join(__dirname, '/')
      },
      compress: true,
      port: 3000,
      hot: true,
      open: true,
      historyApiFallback: true,
      proxy: {
        '/api': {
          target: process.env.REACT_APP_API_URL || 'http://localhost:8000',
          changeOrigin: true
        },
        '/ws': {
          target: process.env.REACT_APP_WS_URL || 'ws://localhost:8000',
          ws: true,
          changeOrigin: true
        }
      }
    },
    
    performance: {
      hints: isProduction ? 'warning' : false,
      maxEntrypointSize: 512000,
      maxAssetSize: 512000
    },
    
    devtool: isProduction ? 'source-map' : 'eval-source-map'
  };
};